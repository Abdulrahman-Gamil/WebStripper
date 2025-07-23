import os
import csv
import sqlite3
import platform
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import shutil
import glob


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class BrowserHistoryExtractor:
    def __init__(self):
        # Initialize extractor with system info
        self.system = platform.system()
        self.history_data = []

    def get_browser_paths(self):
        # Return default history file paths
        paths = {}
        if self.system == "Windows":
            local_app_data = os.environ.get("LOCALAPPDATA", "")
            app_data = os.environ.get("APPDATA", "")
            paths = {
                "Chrome": os.path.join(local_app_data, "Google", "Chrome", "User Data"),
                "Brave": os.path.join(
                    local_app_data, "BraveSoftware", "Brave-Browser", "User Data"
                ),
                "Edge": os.path.join(local_app_data, "Microsoft", "Edge", "User Data"),
                "Opera": os.path.join(app_data, "Opera Software", "Opera Stable"),
                "Firefox": os.path.join(app_data, "Mozilla", "Firefox", "Profiles"),
            }
        elif self.system == "Linux":
            home = os.path.expanduser("~")
            paths = {
                "Chrome": os.path.join(home, ".config", "google-chrome"),
                "Brave": os.path.join(
                    home, ".config", "BraveSoftware", "Brave-Browser"
                ),
                "Edge": os.path.join(home, ".config", "microsoft-edge"),
                "Opera": os.path.join(home, ".config", "opera"),
                "Firefox": os.path.join(home, ".mozilla", "firefox"),
            }
        elif self.system == "Darwin":
            home = os.path.expanduser("~")
            paths = {
                "Chrome": os.path.join(
                    home, "Library", "Application Support", "Google", "Chrome"
                ),
                "Brave": os.path.join(
                    home,
                    "Library",
                    "Application Support",
                    "BraveSoftware",
                    "Brave-Browser",
                ),
                "Edge": os.path.join(
                    home, "Library", "Application Support", "Microsoft Edge"
                ),
                "Opera": os.path.join(
                    home, "Library", "Application Support", "com.operasoftware.Opera"
                ),
                "Firefox": os.path.join(
                    home, "Library", "Application Support", "Firefox", "Profiles"
                ),
            }
        return paths

    def find_chromium_profiles(self, base_path):
        # Find all Chromium profile directories containing History files
        history_files = []
        if not os.path.exists(base_path):
            return history_files
        try:
            for item in os.listdir(base_path):
                profile_path = os.path.join(base_path, item)
                if os.path.isdir(profile_path) and (
                    item.startswith("Profile") or item == "Default"
                ):
                    history_db = os.path.join(profile_path, "History")
                    if os.path.exists(history_db):
                        history_files.append(history_db)
        except PermissionError:
            pass
        return history_files

    def find_firefox_profiles(self, firefox_dir):
        # Find Firefox profile directories
        history_files = []
        if not os.path.exists(firefox_dir):
            return history_files
        try:
            for item in os.listdir(firefox_dir):
                profile_path = os.path.join(firefox_dir, item)
                if os.path.isdir(profile_path) and (
                    "default" in item.lower() or len(item) > 8
                ):
                    places_db = os.path.join(profile_path, "places.sqlite")
                    if os.path.exists(places_db):
                        history_files.append(places_db)
        except PermissionError:
            pass
        return history_files

    def extract_chromium_history(self, history_file, browser_name):
        # Extract history from Chromium database
        entries = []
        if not os.path.exists(history_file):
            return entries
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
                temp_file = tmp.name
                shutil.copy2(history_file, temp_file)
            conn = sqlite3.connect(temp_file)
            cursor = conn.cursor()
            query = """
            SELECT url, title, visit_count, last_visit_time
            FROM urls
            WHERE last_visit_time > 0
            ORDER BY last_visit_time DESC
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            for row in rows:
                url, title, visit_count, last_visit_time = row
                if last_visit_time:
                    try:
                        unix_timestamp = (last_visit_time - 11644473600000000) / 1000000
                        dt = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
                        entries.append(
                            {
                                "browser": browser_name,
                                "url": url,
                                "title": title or "",
                                "visit_count": visit_count,
                                "date": dt.strftime("%Y-%m-%d"),
                                "time": dt.strftime("%H:%M:%S"),
                                "datetime": dt,
                            }
                        )
                    except (ValueError, OSError):
                        continue
            conn.close()
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
        return entries

    def extract_firefox_history(self, places_file):
        # Extract history from Firefox database
        entries = []
        if not os.path.exists(places_file):
            return entries
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
                temp_file = tmp.name
                shutil.copy2(places_file, temp_file)
            conn = sqlite3.connect(temp_file)
            cursor = conn.cursor()
            query = """
            SELECT p.url, p.title, h.visit_date, p.visit_count
            FROM moz_places p
            JOIN moz_historyvisits h ON p.id = h.place_id
            WHERE h.visit_date IS NOT NULL
            ORDER BY h.visit_date DESC
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            for row in rows:
                url, title, visit_date, visit_count = row
                if visit_date:
                    try:
                        dt = datetime.fromtimestamp(
                            visit_date / 1000000, tz=timezone.utc
                        )
                        entries.append(
                            {
                                "browser": "Firefox",
                                "url": url,
                                "title": title or "",
                                "visit_count": visit_count,
                                "date": dt.strftime("%Y-%m-%d"),
                                "time": dt.strftime("%H:%M:%S"),
                                "datetime": dt,
                            }
                        )
                    except (ValueError, OSError):
                        continue
            conn.close()
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
        return entries

    def save_to_csv(self, entries, filename):
        # Save history entries to CSV
        if not entries:
            return
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["Browser", "URL", "Date", "Time", "Title", "Visit_Count"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for entry in entries:
                writer.writerow(
                    {
                        "Browser": entry["browser"],
                        "URL": entry["url"],
                        "Date": entry["date"],
                        "Time": entry["time"],
                        "Title": entry["title"],
                        "Visit_Count": entry["visit_count"],
                    }
                )
