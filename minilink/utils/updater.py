# minilink/utils/updater.py

import requests
import sys
import os
import shutil
import tempfile
from tkinter import messagebox
import re

GITHUB_REPO = "xNycrofox/minilink"
CURRENT_VERSION = "0.0.1"

def parse_version(version):
    """Extrahiert die Versionsnummer aus dem tag_name-Format."""
    print(tuple(map(int, re.sub(r'[^0-9.]', '', version).split('.'))))
    return tuple(map(int, re.sub(r'[^0-9.]', '', version).split('.')))

def check_for_update():
    """Überprüft auf Updates und bietet dem Benutzer ein Update an."""
    try:
        response = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest")
        response.raise_for_status()
        latest_release = response.json()
        latest_version = latest_release['tag_name']

        if parse_version(latest_version) > parse_version(CURRENT_VERSION):
            answer = messagebox.askyesno(
                "Update verfügbar",
                f"Version {latest_version} ist verfügbar. Möchtest du das Update installieren?"
            )
            if answer:
                download_url = next(
                    asset['browser_download_url']
                    for asset in latest_release['assets']
                    if asset['name'].endswith('.exe') or asset['name'].endswith('.pkg') or asset['name'].endswith('.sh')
                )
                download_and_replace(download_url, latest_version)
    except Exception as e:
        print(f"Update-Überprüfung fehlgeschlagen: {e}")


def download_and_replace(download_url, version):
    """Lädt die neue Version herunter und ersetzt das aktuelle Programm."""
    try:
        temp_dir = tempfile.mkdtemp()
        if sys.platform == 'win32':
            file_ext = '.exe'
        elif sys.platform == 'darwin':
            file_ext = '.app'
        else:
            file_ext = '.sh'  # Oder passendes Format

        temp_file = os.path.join(temp_dir, f"minilink_{version}{file_ext}")
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(temp_file, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

        current_executable = sys.argv[0]
        shutil.move(temp_file, current_executable)
        messagebox.showinfo("Update abgeschlossen", "Minilink wurde aktualisiert. Bitte starte die Anwendung neu.")
        sys.exit(0)
    except Exception as e:
        messagebox.showerror("Update fehlgeschlagen", f"Das Update konnte nicht installiert werden: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
