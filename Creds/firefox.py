import os
import ctypes
import base64
import json
import csv
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama for colored console output
init()


class FirefoxPasswordExtractor:
    def __init__(self, profile_path: str = None):
        """Initialize Firefox password extractor with optional custom profile path."""
        self.browser_name = "Firefox"
        self.profile_path = (
            profile_path if profile_path else self.get_firefox_profile_path()
        )
        self.nss_library = None
        self.initialize_nss()

    def get_firefox_profile_path(self) -> str:
        """Find a Firefox profile directory in Windows."""
        user_home = Path(os.environ.get("USERPROFILE", "C:\\Users\\Default"))
        possible_base_dirs = [
            user_home / "AppData" / "Roaming" / "Mozilla" / "Firefox" / "Profiles",
            user_home / "AppData" / "Local" / "Mozilla" / "Firefox" / "Profiles",
            user_home
            / "AppData"
            / "Local"
            / "Packages"
            / "Mozilla.Firefox_n80bbvh6b1yt2"
            / "LocalCache"
            / "Local"
            / "Mozilla"
            / "Firefox"
            / "Profiles",
        ]

        for base_dir in possible_base_dirs:
            if base_dir.exists():
                profiles = list(base_dir.glob("*.default*"))
                if profiles:
                    return str(profiles[0])
                profiles = [d for d in base_dir.iterdir() if d.is_dir()]
                if profiles:
                    return str(profiles[0])

        raise FileNotFoundError(
            f"{Fore.RED}No Firefox profile found in any possible directory.{Style.RESET_ALL}"
        )

    def get_all_profile_paths(self) -> list:
        """Retrieve all Firefox profile directories."""
        user_home = Path(os.environ.get("USERPROFILE", "C:\\Users\\Default"))
        possible_base_dirs = [
            user_home / "AppData" / "Roaming" / "Mozilla" / "Firefox" / "Profiles",
            user_home / "AppData" / "Local" / "Mozilla" / "Firefox" / "Profiles",
            user_home
            / "AppData"
            / "Local"
            / "Packages"
            / "Mozilla.Firefox_n80bbvh6b1yt2"
            / "LocalCache"
            / "Local"
            / "Mozilla"
            / "Firefox"
            / "Profiles",
        ]
        profiles = []
        for base_dir in possible_base_dirs:
            if base_dir.exists():
                for folder in base_dir.iterdir():
                    if folder.is_dir() and ".default" in folder.name:
                        logins_json_path = folder / "logins.json"
                        if logins_json_path.exists():
                            profiles.append((str(folder), folder.name))
        return profiles

    def initialize_nss(self) -> bool:
        """Initialize NSS library for Firefox password decryption."""
        try:
            firefox_dir = "C:\\Program Files\\Mozilla Firefox"
            if not os.path.exists(firefox_dir):
                firefox_dir = "C:\\Program Files (x86)\\Mozilla Firefox"
                if not os.path.exists(firefox_dir):
                    print(
                        f"{Fore.RED}Firefox installation directory not found{Style.RESET_ALL}"
                    )
                    return False
            os.environ["PATH"] = firefox_dir + ";" + os.environ["PATH"]
            self.nss_library = ctypes.CDLL(os.path.join(firefox_dir, "nss3.dll"))
            if self.nss_library.NSS_Init(self.profile_path.encode("utf-8")) != 0:
                return False
            return True
        except Exception as e:
            print(f"{Fore.RED}Failed to initialize NSS: {str(e)}{Style.RESET_ALL}")
            return False

    def shutdown_nss(self):
        """Shutdown NSS library to release resources."""
        if self.nss_library:
            try:
                self.nss_library.NSS_Shutdown()
            except Exception as e:
                print(f"{Fore.RED}Error shutting down NSS: {str(e)}{Style.RESET_ALL}")

    def decrypt_firefox_password(self, encrypted_data: str) -> str:
        """Decrypt a Firefox password using the NSS library."""

        class SECItem(ctypes.Structure):
            _fields_ = [
                ("type", ctypes.c_uint),
                ("data", ctypes.POINTER(ctypes.c_ubyte)),
                ("len", ctypes.c_uint),
            ]

        try:
            decoded_data = base64.b64decode(encrypted_data)
            item = SECItem(
                0,
                ctypes.cast(
                    ctypes.create_string_buffer(decoded_data),
                    ctypes.POINTER(ctypes.c_ubyte),
                ),
                len(decoded_data),
            )
            decrypted_item = SECItem()
            if (
                self.nss_library.PK11SDR_Decrypt(
                    ctypes.byref(item), ctypes.byref(decrypted_item), None
                )
                == 0
            ):
                return ctypes.string_at(decrypted_item.data, decrypted_item.len).decode(
                    "utf-8"
                )
            return f"{Fore.RED}[Failed to decrypt]{Style.RESET_ALL}"
        except Exception as e:
            print(f"{Fore.RED}Error decrypting password: {str(e)}{Style.RESET_ALL}")
            return f"{Fore.RED}[Failed to decrypt]{Style.RESET_ALL}"

    def extract_passwords(self, output_path=None):
        """Extract passwords from all Firefox profiles and return credentials list."""
        credentials = []
        profile_paths = (
            [(self.profile_path, os.path.basename(self.profile_path))]
            if os.path.isfile(os.path.join(self.profile_path, "logins.json"))
            else self.get_all_profile_paths()
        )

        for profile_path, profile_name in profile_paths:
            if not self.initialize_nss():
                continue
            logins_json_path = os.path.join(profile_path, "logins.json")
            if not os.path.exists(logins_json_path):
                print(
                    f"{Fore.RED}No logins.json found in {profile_path}{Style.RESET_ALL}"
                )
                self.shutdown_nss()
                continue

            print(
                f"{Fore.CYAN}Extracting from Firefox profile: {profile_name}{Style.RESET_ALL}"
            )
            try:
                with open(logins_json_path, "r", encoding="utf-8") as f:
                    logins = json.load(f)
            except Exception as e:
                print(f"{Fore.RED}Error reading logins.json: {str(e)}{Style.RESET_ALL}")
                self.shutdown_nss()
                continue

            for login in logins.get("logins", []):
                url = login.get("hostname", "")
                encrypted_username = login.get("encryptedUsername", "")
                encrypted_password = login.get("encryptedPassword", "")
                username = self.decrypt_firefox_password(encrypted_username)
                password = self.decrypt_firefox_password(encrypted_password)
                if (
                    username
                    and password
                    and not username.startswith(f"{Fore.RED}")
                    and not password.startswith(f"{Fore.RED}")
                ):
                    credentials.append(
                        {
                            "browser": self.browser_name,
                            "profile": profile_name,
                            "url": url,
                            "username": username,
                            "password": password,
                        }
                    )

            self.shutdown_nss()

        return credentials
