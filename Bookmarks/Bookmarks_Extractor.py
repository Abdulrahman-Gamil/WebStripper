import json
import sqlite3
import csv
import os
import glob
from colorama import init, Fore, Style

init(autoreset=True)


def extract_chromium_bookmarks(file_path, browser, profile):
    # Extract bookmarks from Chromium JSON file
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        bookmarks = []

        def traverse(node, path=""):
            if not isinstance(node, dict) or "type" not in node:
                return
            node_type = node["type"]
            node_name = node.get("name", "Untitled")
            if node_type == "url":
                bookmarks.append(
                    {
                        "browser": browser,
                        "profile": profile,
                        "title": node_name,
                        "url": node.get("url", ""),
                    }
                )
            elif node_type == "folder":
                for child in node.get("children", []):
                    traverse(child, f"{path}/{node_name}" if path else node_name)

        for root_name, root_node in data.get("roots", {}).items():
            traverse(root_node, f"roots/{root_name}")
        return bookmarks, f"Extracted {len(bookmarks)} bookmarks"
    except Exception as e:
        return [], str(e)


def extract_firefox_bookmarks(file_path, browser, profile):
    # Extract bookmarks from Firefox database
    try:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        query = """
        SELECT moz_bookmarks.title, moz_places.url
        FROM moz_bookmarks
        JOIN moz_places ON moz_bookmarks.fk = moz_places.id
        WHERE moz_bookmarks.type = 1 AND moz_places.url IS NOT NULL
        """
        cursor.execute(query)
        bookmarks = [
            {
                "browser": browser,
                "profile": profile,
                "title": row[0] if row[0] else "Untitled",
                "url": row[1],
            }
            for row in cursor.fetchall()
        ]
        conn.close()
        return bookmarks, f"Extracted {len(bookmarks)} bookmarks"
    except Exception as e:
        return [], str(e)


def get_all_bookmark_files():
    # Find all bookmark files for supported browsers
    browser_paths = {
        "Chrome": os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
        "Edge": os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data"),
        "Brave": os.path.expandvars(
            r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data"
        ),
        "Opera": os.path.expandvars(r"%APPDATA%\Opera Software\Opera Stable"),
        "Firefox": os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles"),
    }
    all_files = []
    for browser, base_path in browser_paths.items():
        if not os.path.exists(base_path):
            continue
        if browser == "Firefox":
            profiles = glob.glob(os.path.join(base_path, "*.default*"))
            for profile in profiles:
                places_file = os.path.join(profile, "places.sqlite")
                if os.path.isfile(places_file):
                    all_files.append((browser, os.path.basename(profile), places_file))
        else:
            root_bookmarks = os.path.join(base_path, "Bookmarks")
            if os.path.isfile(root_bookmarks):
                all_files.append((browser, "Root", root_bookmarks))
            profiles = glob.glob(os.path.join(base_path, "*"))
            for profile in profiles:
                if os.path.isdir(profile):
                    bookmarks_file = os.path.join(profile, "Bookmarks")
                    if os.path.isfile(bookmarks_file):
                        all_files.append(
                            (browser, os.path.basename(profile), bookmarks_file)
                        )
    return all_files
