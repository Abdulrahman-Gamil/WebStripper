import sqlite3
import os
import glob
import tempfile
import shutil
from datetime import datetime, timezone


def extract_chromium_autofill(db_path):
    # Extract autofill data from Chromium Web Data database
    entries = []
    if not os.path.exists(db_path):
        return entries
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            temp_file = tmp.name
            shutil.copy2(db_path, temp_file)
        conn = sqlite3.connect(temp_file)
        cursor = conn.cursor()
        query = """
        SELECT name, value, date_created
        FROM autofill
        WHERE value IS NOT NULL
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            name, value, date_created = row
            try:
                dt = (
                    datetime.fromtimestamp(date_created, tz=timezone.utc)
                    if date_created
                    else None
                )
                entries.append({"field": name, "value": value, "date": dt})
            except (ValueError, OSError):
                continue
        conn.close()
    finally:
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
    return entries


def extract_firefox_autofill(db_path):
    # Extract autofill data from Firefox formhistory.sqlite
    entries = []
    if not os.path.exists(db_path):
        return entries
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            temp_file = tmp.name
            shutil.copy2(db_path, temp_file)
        conn = sqlite3.connect(temp_file)
        cursor = conn.cursor()
        query = """
        SELECT fieldname, value, firstUsed
        FROM moz_formhistory
        WHERE value IS NOT NULL
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            fieldname, value, first_used = row
            try:
                dt = (
                    datetime.fromtimestamp(first_used / 1000000, tz=timezone.utc)
                    if first_used
                    else None
                )
                entries.append({"field": fieldname, "value": value, "date": dt})
            except (ValueError, OSError):
                continue
        conn.close()
    finally:
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
    return entries


def find_chromium_profiles():
    # Find all Chromium profile directories containing Web Data files
    browser_paths = {
        "Chrome": os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
        "Edge": os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data"),
        "Brave": os.path.expandvars(
            r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data"
        ),
        "Opera": os.path.expandvars(r"%APPDATA%\Opera Software\Opera Stable"),
    }
    all_files = []
    for browser, base_path in browser_paths.items():
        if not os.path.exists(base_path):
            continue
        root_web_data = os.path.join(base_path, "Web Data")
        if os.path.isfile(root_web_data):
            all_files.append((browser, "Root", root_web_data))
        profiles = glob.glob(os.path.join(base_path, "*"))
        for profile in profiles:
            if os.path.isdir(profile):
                web_data_file = os.path.join(profile, "Web Data")
                if os.path.isfile(web_data_file):
                    all_files.append(
                        (browser, os.path.basename(profile), web_data_file)
                    )
    return all_files


def find_firefox_profiles():
    # Find Firefox profile directories
    firefox_dir = os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles")
    history_files = []
    if not os.path.exists(firefox_dir):
        return history_files
    try:
        profiles = glob.glob(os.path.join(firefox_dir, "*.default*"))
        for profile in profiles:
            places_db = os.path.join(profile, "formhistory.sqlite")
            if os.path.isfile(places_db):
                history_files.append(("Firefox", os.path.basename(profile), places_db))
    except PermissionError:
        pass
    return history_files
