import argparse
import os
import json
import base64
import binascii
from pathlib import Path
from colorama import init, Fore, Style
from Autofill.Autofill_Data_Extractor import (
    extract_chromium_autofill,
    extract_firefox_autofill,
    find_chromium_profiles,
    find_firefox_profiles,
)
from Bookmarks.Bookmarks_Extractor import (
    extract_chromium_bookmarks,
    extract_firefox_bookmarks,
    get_all_bookmark_files,
)
from History.History_Extractor import BrowserHistoryExtractor
from Creds.chrome import ChromePasswordExtractor
from Creds.brave import BravePasswordExtractor
from Creds.edge import EdgePasswordExtractor
from Creds.opera import OperaPasswordExtractor
from Creds.firefox import FirefoxPasswordExtractor
from Creds.chrome_wkey import ChromeWKeyPasswordExtractor
from Creds.brave_wkey import BraveWKeyPasswordExtractor
from Creds.edge_wkey import EdgeWKeyPasswordExtractor
from Creds.opera_wkey import OperaWKeyPasswordExtractor

init(autoreset=True)


def display_startup():
    # Display ASCII logo, disclaimer, and credit
    logo = rf"""
{Fore.YELLOW}{Style.BRIGHT}
###############################################################
#__          __  _     _____ _        _                       #
#\ \        / / | |   / ____| |      (_)                      #
# \ \  /\  / /__| |__| (___ | |_ _ __ _ _ __  _ __   ___ _ __ #
#  \ \/  \/ / _ \ '_ \\___ \| __| '__| | '_ \| '_ \ / _ \ '__|#
#   \  /\  /  __/ |_) |___) | |_| |  | | |_) | |_) |  __/ |   #
#    \/  \/ \___|_.__/_____/ \__|_|  |_| .__/| .__/ \___|_|   #
#                                      | |   | |              #
#                                      |_|   |_|              #
#                                                             #
#                      Made By 0x41474D                       #
#                 github.com/Abdulrahman-Gamil                #
###############################################################
"""
    print(logo)
    print(
        f"{Fore.RED}{Style.BRIGHT}###############################################################{Style.RESET_ALL}"
    )
    print(
        f"{Fore.RED}{Style.BRIGHT}#                     DISCLAIMER NOTICE                       #{Style.RESET_ALL}"
    )
    print(
        f"{Fore.RED}{Style.BRIGHT}#   WebStripper Tool is intended for ethical use only.        #{Style.RESET_ALL}"
    )
    print(
        f"{Fore.RED}{Style.BRIGHT}#   Misuse of WebStripper may violate local or global laws.   #{Style.RESET_ALL}"
    )
    print(
        f"{Fore.RED}{Style.BRIGHT}#   The creator accept no responsibility for any misuse.      #{Style.RESET_ALL}"
    )
    print(
        f"{Fore.RED}{Style.BRIGHT}###############################################################{Style.RESET_ALL}"
    )

    input(f"{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")


def get_default_paths(data_type):
    # Return default paths for browsers based on data type
    local = os.environ.get("LOCALAPPDATA", "")
    appdata = os.environ.get("APPDATA", "")
    paths = {
        "Chrome": os.path.join(local, "Google", "Chrome", "User Data"),
        "Brave": os.path.join(local, "BraveSoftware", "Brave-Browser", "User Data"),
        "Edge": os.path.join(local, "Microsoft", "Edge", "User Data"),
        "Opera": os.path.join(appdata, "Opera Software", "Opera Stable"),
        "Firefox": os.path.join(appdata, "Mozilla", "Firefox", "Profiles"),
    }
    return paths


def display_path_info(data_type):
    # Display default paths for all browsers for the given data type
    paths = get_default_paths(data_type)
    print(f"{Fore.YELLOW}Default {data_type.capitalize()} Paths:{Style.RESET_ALL}")
    for browser, path in paths.items():
        print(f"{Fore.BLUE}{browser}: {path}{Style.RESET_ALL}")


def validate_output_path(output_path, browser, data_type):
    # Validate and create output directory, return path or default
    if output_path:
        output_dir = os.path.dirname(output_path) or "."
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        return output_path
    return f"{browser.lower()}_{data_type}.csv"


def display_history_records(entries):
    # Display history records in a colored, organized format
    print(f"{Fore.YELLOW}{Style.BRIGHT}Extracted History Records:{Style.RESET_ALL}")
    print(
        f"{Fore.CYAN}{'Browser':<15} {'URL':<50} {'Title':<50} {'Date':<12} {'Time':<10} {'Visit Count':<12}{Style.RESET_ALL}"
    )
    print("-" * 150)
    for entry in entries:
        print(
            f"{
                Fore.GREEN}{entry['browser']:<15} {
                    Fore.BLUE}{entry['url'][:49]:<50} {
                        entry['title'][:49]:<50} {
                            entry['date']:<12} {entry['time']:<10} {
                                entry['visit_count']:<12}{Style.RESET_ALL}"
        )


def display_bookmark_records(bookmarks):
    # Display bookmark records in a colored, organized format
    print(f"{Fore.YELLOW}{Style.BRIGHT}Extracted Bookmarks:{Style.RESET_ALL}")
    print(
        f"{Fore.CYAN}{'Browser':<15} {'Profile':<20} {'Title':<50} {'URL':<50}{Style.RESET_ALL}"
    )
    print("-" * 135)
    for bookmark in bookmarks:
        print(
            f"{Fore.GREEN}{bookmark['browser']:<15} {
                bookmark['profile']:<20} {bookmark['title'][:49]:<50} {Fore.BLUE}{
                    bookmark['url'][:49]:<50}{Style.RESET_ALL}"
        )


def display_autofill_records(entries):
    # Display autofill records in a colored, organized format
    print(f"{Fore.YELLOW}{Style.BRIGHT}Extracted Autofill Records:{Style.RESET_ALL}")
    print(
        f"{Fore.CYAN}{'Browser':<15} {'Profile':<20} {'Field':<30} {'Value':<50} {'Date':<12} {'Time':<10}{Style.RESET_ALL}"
    )
    print("-" * 137)
    for entry in entries:
        date_str = entry["date"].strftime("%Y-%m-%d") if entry["date"] else ""
        time_str = entry["date"].strftime("%H:%M:%S") if entry["date"] else ""
        print(
            f"{Fore.GREEN}{entry['browser']:<15} {
                entry['profile']:<20} {entry['field'][:29]:<30} {Fore.BLUE}{
                    entry['value'][:49]:<50} {date_str:<12} {time_str:<10}{Style.RESET_ALL}"
        )


def display_credentials_records(credentials):
    # Display credentials in a colored, organized format
    print(f"{Fore.YELLOW}{Style.BRIGHT}Extracted Credentials:{Style.RESET_ALL}")
    print(
        f"{Fore.CYAN}{'Browser':<15} {'Profile':<20} {'URL':<50} {'Username':<30} {'Password':<30}{Style.RESET_ALL}"
    )
    print("-" * 145)
    for cred in credentials:
        print(
            f"{Fore.GREEN}{cred['browser']:<15} {
                cred['profile']:<20} {Fore.BLUE}{cred['url'][:49]:<50} {
                    cred['username'][:29]:<30} {cred['password'][:29]:<30}{Style.RESET_ALL}"
        )


def extract_encrypted_key(browser_name, input_path):
    # Extract the encrypted key from Local State, decode base64, remove first 5 bytes, and save it
    try:
        local_state_path = os.path.join(input_path, "Local State")
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.loads(f.read())
        encrypted_key_b64 = local_state["os_crypt"]["encrypted_key"]
        # Decode base64 key
        encrypted_key = base64.b64decode(encrypted_key_b64)
        # Remove the first 5 bytes (DPAPI prefix)
        encrypted_key = encrypted_key[5:]
        output_file = f"{browser_name.lower()}_key_enc.dat"
        with open(output_file, "wb") as f:
            f.write(encrypted_key)
        print(
            f"{Fore.YELLOW}The encrypted key was saved to {output_file} "
            f"You must decrypt it using the original system's DPAPI master key. "
            f"Once decrypted, rerun this tool using the -key switch with the hex-encoded decrypted key to extract credentials.{Style.RESET_ALL}"
        )
    except Exception as e:
        print(f"{Fore.RED}Error extracting encrypted key: {str(e)}{Style.RESET_ALL}")


def extract_history(browser, input_path, output_path):
    # Extract browsing history for the specified browser
    extractor = BrowserHistoryExtractor()
    entries = []
    if input_path:
        if browser == "f":
            if os.path.isdir(input_path):
                for profile_path in extractor.find_firefox_profiles(input_path):
                    entries.extend(extractor.extract_firefox_history(profile_path))
            else:
                entries = extractor.extract_firefox_history(input_path)
        else:
            browser_name = {"c": "Chrome", "b": "Brave", "e": "Edge", "o": "Opera"}[
                browser
            ]
            if os.path.isdir(input_path):
                for profile_path in extractor.find_chromium_profiles(input_path):
                    entries.extend(
                        extractor.extract_chromium_history(profile_path, browser_name)
                    )
            else:
                entries = extractor.extract_chromium_history(input_path, browser_name)
    else:
        paths = get_default_paths("history")
        if browser == "f":
            for profile in extractor.find_firefox_profiles(paths["Firefox"]):
                entries.extend(extractor.extract_firefox_history(profile))
        else:
            browser_name = {"c": "Chrome", "b": "Brave", "e": "Edge", "o": "Opera"}[
                browser
            ]
            for profile_path in extractor.find_chromium_profiles(paths[browser_name]):
                entries.extend(
                    extractor.extract_chromium_history(profile_path, browser_name)
                )

    if not entries:
        print(f"{Fore.RED}No history records found.{Style.RESET_ALL}")
        return

    if output_path:
        extractor.save_to_csv(entries, output_path)
        print(f"{Fore.GREEN}Extraction completed: {output_path}{Style.RESET_ALL}")
    elif len(entries) > 100:
        print(
            f"{Fore.YELLOW}{len(entries)} records were found. Do you want to save the results to a CSV file? (y/n){Style.RESET_ALL}"
        )
        choice = input().strip().lower()
        if choice == "y":
            default_path = validate_output_path(
                None,
                {
                    "c": "Chrome",
                    "b": "Brave",
                    "e": "Edge",
                    "o": "Opera",
                    "f": "Firefox",
                }[browser],
                "history",
            )
            extractor.save_to_csv(entries, default_path)
            print(f"{Fore.GREEN}Extraction completed: {default_path}{Style.RESET_ALL}")
        else:
            display_history_records(entries)
    else:
        display_history_records(entries)


def extract_bookmarks(browser, input_path, output_path):
    # Extract bookmarks for the specified browser
    bookmarks = []
    browser_name = {
        "c": "Chrome",
        "b": "Brave",
        "e": "Edge",
        "o": "Opera",
        "f": "Firefox",
    }[browser]
    if input_path:
        bookmark_type, file_path = detect_bookmark_type(input_path)
        profile = (
            os.path.basename(os.path.dirname(file_path))
            if os.path.dirname(file_path)
            else "Default"
        )
        if bookmark_type == "chromium":
            bookmarks_part, _ = extract_chromium_bookmarks(
                file_path, browser_name, profile
            )
            bookmarks.extend(bookmarks_part)
        elif bookmark_type == "firefox":
            bookmarks_part, _ = extract_firefox_bookmarks(
                file_path, browser_name, profile
            )
            bookmarks.extend(bookmarks_part)
    else:
        paths = get_default_paths("bookmarks")
        if browser == "f":
            for _, profile, file_path in get_all_bookmark_files():
                if os.path.dirname(file_path).startswith(paths["Firefox"]):
                    bookmarks_part, _ = extract_firefox_bookmarks(
                        file_path, browser_name, profile
                    )
                    bookmarks.extend(bookmarks_part)
        else:
            for b, profile, file_path in get_all_bookmark_files():
                if b == browser_name or (
                    browser_name == "Opera" and b in ["Opera", "Opera GX"]
                ):
                    bookmarks_part, _ = extract_chromium_bookmarks(
                        file_path, browser_name, profile
                    )
                    bookmarks.extend(bookmarks_part)

    if not bookmarks:
        print(f"{Fore.RED}No bookmarks found.{Style.RESET_ALL}")
        return

    if output_path:
        save_to_csv(bookmarks, output_path)
        print(f"{Fore.GREEN}Extraction completed: {output_path}{Style.RESET_ALL}")
    elif len(bookmarks) > 100:
        print(
            f"{Fore.YELLOW}{len(bookmarks)} bookmarks were found. Do you want to save the results to a CSV file? (y/n){Style.RESET_ALL}"
        )
        choice = input().strip().lower()
        if choice == "y":
            default_path = validate_output_path(None, browser_name.lower(), "bookmarks")
            save_to_csv(bookmarks, default_path)
            print(f"{Fore.GREEN}Extraction completed: {default_path}{Style.RESET_ALL}")
        else:
            display_bookmark_records(bookmarks)
    else:
        display_bookmark_records(bookmarks)


def extract_autofill(browser, input_path, output_path):
    entries = []
    browser_name = {
        "c": "Chrome",
        "b": "Brave",
        "e": "Edge",
        "o": "Opera",
        "f": "Firefox",
    }[browser]
    if input_path:
        if os.path.isdir(input_path):
            # Handle directory input by finding Web Data files
            for b, profile, db_path in (
                find_chromium_profiles() if browser != "f" else find_firefox_profiles()
            ):
                if os.path.dirname(db_path).startswith(os.path.abspath(input_path)):
                    if browser == "f":
                        data = extract_firefox_autofill(db_path)
                        if data:
                            entries.extend(
                                [
                                    {
                                        "browser": browser_name,
                                        "profile": profile,
                                        "field": e["field"],
                                        "value": e["value"],
                                        "date": e["date"],
                                    }
                                    for e in data
                                ]
                            )
                    else:
                        data = extract_chromium_autofill(db_path)
                        if data:
                            entries.extend(
                                [
                                    {
                                        "browser": browser_name,
                                        "profile": profile,
                                        "field": e["field"],
                                        "value": e["value"],
                                        "date": e["date"],
                                    }
                                    for e in data
                                ]
                            )
        else:
            # Handle file input
            profile = (
                os.path.basename(os.path.dirname(input_path))
                if os.path.dirname(input_path)
                else "Default"
            )
            if browser == "f":
                data = extract_firefox_autofill(input_path)
                if data:
                    entries.extend(
                        [
                            {
                                "browser": browser_name,
                                "profile": profile,
                                "field": e["field"],
                                "value": e["value"],
                                "date": e["date"],
                            }
                            for e in data
                        ]
                    )
            else:
                data = extract_chromium_autofill(input_path)
                if data:
                    entries.extend(
                        [
                            {
                                "browser": browser_name,
                                "profile": profile,
                                "field": e["field"],
                                "value": e["value"],
                                "date": e["date"],
                            }
                            for e in data
                        ]
                    )
    else:
        paths = get_default_paths("autofill")
        if browser == "f":
            for _, profile, db_path in find_firefox_profiles():
                if os.path.dirname(db_path).startswith(paths["Firefox"]):
                    data = extract_firefox_autofill(db_path)
                    if data:
                        entries.extend(
                            [
                                {
                                    "browser": browser_name,
                                    "profile": profile,
                                    "field": e["field"],
                                    "value": e["value"],
                                    "date": e["date"],
                                }
                                for e in data
                            ]
                        )
        else:
            for b, profile, db_path in find_chromium_profiles():
                if b == browser_name or (
                    browser_name == "Opera" and b in ["Opera", "Opera GX"]
                ):
                    data = extract_chromium_autofill(db_path)
                    if data:
                        entries.extend(
                            [
                                {
                                    "browser": browser_name,
                                    "profile": profile,
                                    "field": e["field"],
                                    "value": e["value"],
                                    "date": e["date"],
                                }
                                for e in data
                            ]
                        )

    if not entries:
        print(f"{Fore.RED}No autofill records found.{Style.RESET_ALL}")
        return

    if output_path:
        write_csv(entries, output_path)
        print(f"{Fore.GREEN}Extraction completed: {output_path}{Style.RESET_ALL}")
    elif len(entries) > 100:
        print(
            f"{Fore.YELLOW}{len(entries)} autofill records were found. Do you want to save the results to a CSV file? (y/n){Style.RESET_ALL}"
        )
        choice = input().strip().lower()
        if choice == "y":
            default_path = validate_output_path(None, browser_name.lower(), "autofill")
            write_csv(entries, default_path)
            print(f"{Fore.GREEN}Extraction completed: {default_path}{Style.RESET_ALL}")
        else:
            display_autofill_records(entries)
    else:
        display_autofill_records(entries)


def extract_creds(browser, input_path, output_path, key_path=None):
    # Extract credentials for the specified browser
    extractor_map = {
        "c": ChromePasswordExtractor,
        "b": BravePasswordExtractor,
        "e": EdgePasswordExtractor,
        "o": OperaPasswordExtractor,
        "f": FirefoxPasswordExtractor,
    }
    wkey_extractor_map = {
        "c": ChromeWKeyPasswordExtractor,
        "b": BraveWKeyPasswordExtractor,
        "e": EdgeWKeyPasswordExtractor,
        "o": OperaWKeyPasswordExtractor,
    }
    browser_name = {
        "c": "Chrome",
        "b": "Brave",
        "e": "Edge",
        "o": "Opera",
        "f": "Firefox",
    }[browser]
    credentials = []

    # Validate key usage
    if key_path and (browser == "f" or not input_path):
        print(
            f"{Fore.RED}The -key option is only valid with --creds and -in for Chrome, Brave, Edge, or Opera{Style.RESET_ALL}"
        )
        return

    # Handle input path with DPAPI-based browsers
    if input_path and browser in ["c", "b", "e", "o"]:
        if not key_path:
            print(
                f"{Fore.RED}A decrypted key is required to extract credentials from an external User Data directory for {browser_name}. "
                f"Please provide a key using the -key switch.{Style.RESET_ALL}"
            )
            extract_encrypted_key(browser_name, input_path)
            return
        else:
            try:
                # Treat key_path as a hex string and convert to bytes
                secret_key = binascii.unhexlify(key_path)
                extractor = wkey_extractor_map[browser](input_path, secret_key)
                creds = extractor.extract_passwords()
                if creds:
                    credentials.extend(creds)
            except Exception as e:
                print(
                    f"{Fore.RED}Error processing {browser_name} credentials with provided key: {str(e)}{Style.RESET_ALL}"
                )
                return
    else:
        # Handle Firefox or default path cases
        if input_path:
            if browser == "f" and os.path.isdir(input_path):
                for folder in os.listdir(input_path):
                    if ".default" in folder:
                        try:
                            profile_path = os.path.join(input_path, folder)
                            logins_json_path = os.path.join(profile_path, "logins.json")
                            if os.path.exists(logins_json_path):
                                extractor = extractor_map[browser](profile_path)
                                creds = extractor.extract_passwords()
                                if creds:
                                    credentials.extend(creds)
                        except Exception as e:
                            print(
                                f"{Fore.RED}Error processing Firefox profile {folder}: {str(e)}{Style.RESET_ALL}"
                            )
            else:
                try:
                    extractor = extractor_map[browser](input_path)
                    creds = extractor.extract_passwords()
                    if creds:
                        credentials.extend(creds)
                except Exception as e:
                    print(
                        f"{Fore.RED}Error processing input path {input_path}: {str(e)}{Style.RESET_ALL}"
                    )
        else:
            paths = get_default_paths("creds")
            if browser == "f":
                for folder in os.listdir(paths["Firefox"]):
                    if ".default" in folder:
                        try:
                            profile_path = os.path.join(paths["Firefox"], folder)
                            logins_json_path = os.path.join(profile_path, "logins.json")
                            if os.path.exists(logins_json_path):
                                extractor = extractor_map[browser](profile_path)
                                creds = extractor.extract_passwords()
                                if creds:
                                    credentials.extend(creds)
                        except Exception as e:
                            print(
                                f"{Fore.RED}Error processing Firefox profile {folder}: {str(e)}{Style.RESET_ALL}"
                            )
            else:
                try:
                    extractor = extractor_map[browser](paths[browser_name])
                    creds = extractor.extract_passwords()
                    if creds:
                        credentials.extend(creds)
                except Exception as e:
                    print(
                        f"{Fore.RED}Error processing {browser_name} profiles: {str(e)}{Style.RESET_ALL}"
                    )

    if not credentials:
        print(f"{Fore.RED}No credentials found.{Style.RESET_ALL}")
        return

    if output_path:
        save_credentials_to_csv(credentials, output_path)
        print(f"{Fore.GREEN}Extraction completed: {output_path}{Style.RESET_ALL}")
    elif len(credentials) > 100:
        print(
            f"{Fore.YELLOW}{len(credentials)} credentials were found. Do you want to save them to a CSV file? (y/n){Style.RESET_ALL}"
        )
        choice = input().strip().lower()
        if choice == "y":
            default_path = validate_output_path(None, browser_name.lower(), "creds")
            save_credentials_to_csv(credentials, default_path)
            print(f"{Fore.GREEN}Extraction completed: {default_path}{Style.RESET_ALL}")
        else:
            display_credentials_records(credentials)
    else:
        display_credentials_records(credentials)


def detect_bookmark_type(path):
    # Detect bookmark file type
    if os.path.isdir(path):
        bookmarks_file = os.path.join(path, "Bookmarks")
        places_file = os.path.join(path, "places.sqlite")
        if os.path.isfile(bookmarks_file):
            return "chromium", bookmarks_file
        elif os.path.isfile(places_file):
            return "firefox", places_file
        return None, None
    elif os.path.isfile(path):
        if path.endswith("Bookmarks"):
            return "chromium", path
        elif path.endswith("places.sqlite"):
            return "firefox", path
        return None, None
    return None, None


def save_to_csv(bookmarks, csv_file):
    # Save bookmarks to CSV
    import csv

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["browser", "profile", "title", "url"])
        writer.writeheader()
        writer.writerows(bookmarks)


def write_csv(entries, output):
    # Save autofill data to CSV
    import csv

    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Browser", "Profile", "Field", "Value", "Date", "Time"])
        for e in entries:
            date_str = e["date"].strftime("%Y-%m-%d") if e["date"] else ""
            time_str = e["date"].strftime("%H:%M:%S") if e["date"] else ""
            writer.writerow(
                [e["browser"], e["profile"], e["field"], e["value"], date_str, time_str]
            )


def save_credentials_to_csv(credentials, csv_file):
    # Save credentials to CSV
    import csv

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Browser", "Profile", "URL", "Username", "Password"])
        for cred in credentials:
            writer.writerow(
                [
                    cred["browser"],
                    cred["profile"],
                    cred["url"],
                    cred["username"],
                    cred["password"],
                ]
            )


def path():
    TITLE = "\033[94m"
    LABEL = "\033[96m"
    PATH = "\033[97m"
    RESET = "\033[0m"

    print(f"{TITLE}Credentials Input Extraction{RESET}")
    print(
        f"{LABEL}Chrome:{RESET}  {PATH}C:\\Users\\<User>\\AppData\\Local\\Google\\Chrome\\User Data{RESET}"
    )
    print(
        f"{LABEL}Brave:{RESET}   {PATH}C:\\Users\\<User>\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data{RESET}"
    )
    print(
        f"{LABEL}Edge:{RESET}    {PATH}C:\\Users\\<User>\\AppData\\Local\\Microsoft\\Edge\\User Data{RESET}"
    )
    print(
        f"{LABEL}Opera:{RESET}   {PATH}C:\\Users\\<User>\\AppData\\Roaming\\Opera Software\\Opera Stable{RESET}"
    )
    print(
        f"{LABEL}Firefox:{RESET} {PATH}C:\\Users\\<User>\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles{RESET}\n"
    )

    print(f"{TITLE}Browsing History Input Extraction{RESET}")
    print(
        f"{LABEL}Chrome:{RESET}  {PATH}C:\\Users\\<User>\\AppData\\Local\\Google\\Chrome\\User Data{RESET}"
    )
    print(
        f"{LABEL}Brave:{RESET}   {PATH}C:\\Users\\<User>\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data{RESET}"
    )
    print(
        f"{LABEL}Edge:{RESET}    {PATH}C:\\Users\\<User>\\AppData\\Local\\Microsoft\\Edge\\User Data{RESET}"
    )
    print(
        f"{LABEL}Opera:{RESET}   {PATH}C:\\Users\\<User>\\AppData\\Roaming\\Opera Software\\Opera Stable{RESET}"
    )
    print(
        f"{LABEL}Firefox:{RESET} {PATH}C:\\Users\\<User>\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles{RESET}\n"
    )

    print(f"{TITLE}Bookmarks Input Extraction{RESET}")
    print(
        f"{LABEL}Chrome:{RESET}  {PATH}C:\\Users\\<User>\\AppData\\Local\\Google\\Chrome\\User Data\\<Profile>\\Bookmarks{RESET}"
    )
    print(
        f"{LABEL}Brave:{RESET}   {PATH}C:\\Users\\<User>\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data\\<Profile>\\Bookmarks{RESET}"
    )
    print(
        f"{LABEL}Edge:{RESET}    {PATH}C:\\Users\\<User>\\AppData\\Local\\Microsoft\\Edge\\User Data\\<Profile>\\Bookmarks{RESET}"
    )
    print(
        f"{LABEL}Opera:{RESET}   {PATH}C:\\Users\\<User>\\AppData\\Roaming\\Opera Software\\Opera Stable\\<Profile>\\Bookmarks{RESET}"
    )
    print(
        f"{LABEL}Firefox:{RESET} {PATH}C:\\Users\\<User>\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\<Profile>\\places.sqlite{RESET}\n"
    )

    print(f"{TITLE}Autofill Data Input Extraction{RESET}")
    print(
        f"{LABEL}Chrome:{RESET}  {PATH}C:\\Users\\<User>\\AppData\\Local\\Google\\Chrome\\User Data\\<Profile>\\Web Data{RESET}"
    )
    print(
        f"{LABEL}Brave:{RESET}   {PATH}C:\\Users\\<User>\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data\\<Profile>\\Web Data{RESET}"
    )
    print(
        f"{LABEL}Edge:{RESET}    {PATH}C:\\Users\\<User>\\AppData\\Local\\Microsoft\\Edge\\User Data\\<Profile>\\Web Data{RESET}"
    )
    print(
        f"{LABEL}Opera:{RESET}   {PATH}C:\\Users\\<User>\\AppData\\Roaming\\Opera Software\\Opera Stable\\<Profile>\\Web Data{RESET}"
    )
    print(
        f"{LABEL}Firefox:{RESET} {PATH}C:\\Users\\<User>\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\<Profile>\\formhistory.sqlite{RESET}\n"
    )


def main():
    # Main function to parse arguments and control extraction
    display_startup()
    parser = argparse.ArgumentParser(
        description=f"{Fore.YELLOW}WebStripper: Extract browser data for ethical hacking and forensics{Style.RESET_ALL}",
        epilog="",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--history", action="store_true", help="Extract browsing history"
    )
    group.add_argument("--bookmarks", action="store_true", help="Extract bookmarks")
    group.add_argument(
        "--autofill", action="store_true", help="Extract autofill form data"
    )
    group.add_argument("--creds", action="store_true", help="Extract saved credentials")
    parser.add_argument(
        "--browser",
        choices=["c", "b", "e", "o", "f"],
        help="Browser: c=Chrome, b=Brave, e=Edge, o=Opera, f=Firefox",
    )
    parser.add_argument(
        "-in", dest="input_path", help="Custom input path (file or directory)"
    )
    parser.add_argument("-out", dest="output_path", help="Output CSV file path")
    parser.add_argument(
        "--path-info", action="store_true", help="Display default paths and exit"
    )
    parser.add_argument(
        "-key",
        dest="key_path",
        help="Decrypted key (hex string) for credential extraction",
    )
    args = parser.parse_args()

    if args.path_info:
        path()
        return

    if not args.browser:
        parser.error(
            f"{Fore.RED}--browser is required unless --path-info is used{Style.RESET_ALL}"
        )

    data_type = next(
        k
        for k, v in vars(args).items()
        if v and k in ["history", "bookmarks", "autofill", "creds"]
    )
    output_path = validate_output_path(
        args.output_path,
        {"c": "Chrome", "b": "Brave", "e": "Edge", "o": "Opera", "f": "Firefox"}[
            args.browser
        ],
        data_type,
    )

    try:
        if args.history:
            extract_history(args.browser, args.input_path, args.output_path)
        elif args.bookmarks:
            extract_bookmarks(args.browser, args.input_path, args.output_path)
        elif args.autofill:
            extract_autofill(args.browser, args.input_path, args.output_path)
        elif args.creds:
            extract_creds(
                args.browser, args.input_path, args.output_path, args.key_path
            )
    except Exception as e:
        print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
