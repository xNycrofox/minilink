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

def check_for_update(queue, progress_queue):
    """Überprüft auf Updates und bietet dem Benutzer ein Update an."""
    queue.put("Prüfe auf Updates...")
    try:
        response = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest")
        response.raise_for_status()
        latest_release = response.json()
        latest_version = latest_release['tag_name']

        if parse_version(latest_version) > parse_version(CURRENT_VERSION):
            queue.put(f"Update verfügbar: Version {latest_version}")
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
                download_and_replace(download_url, latest_version, progress_queue)
        else:
            queue.put("Version ist aktuell")
    except Exception as e:
        queue.put("Update-Überprüfung fehlgeschlagen")
        print(f"Update-Überprüfung fehlgeschlagen: {e}")



# updater.py

import tempfile
import subprocess
import time
import shutil
import sys
import os

def download_and_replace(download_url, version, progress_queue):
    """Lädt die neue Version herunter und startet den Selbstaktualisierungsprozess."""
    try:
        temp_dir = tempfile.mkdtemp()
        if sys.platform == 'win32':
            file_ext = '.exe'
        elif sys.platform == 'darwin':
            file_ext = '.app'
        else:
            file_ext = ''  # Anpassen für andere Plattformen

        temp_file = os.path.join(temp_dir, f"minilink_{version}{file_ext}")

        # Download der neuen Version (wie bisher)
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        total_length = response.headers.get('content-length')

        if total_length is None:
            with open(temp_file, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
        else:
            total_length = int(total_length)
            downloaded = 0
            chunk_size = 8192
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress = int(100 * downloaded / total_length)
                        progress_queue.put(progress)

        # Pfad zur aktuellen ausführbaren Datei
        if getattr(sys, 'frozen', False):
            current_executable = sys.executable
        else:
            current_executable = sys.argv[0]

        # Starten der neuen ausführbaren Datei mit Update-Parametern
        if sys.platform == 'win32':
            # Windows
            subprocess.Popen([temp_file, '--updating', current_executable], shell=False)
        elif sys.platform == 'darwin':
            # macOS
            subprocess.Popen(['open', temp_file, '--args', '--updating', current_executable])
        else:
            # Linux oder andere
            subprocess.Popen([temp_file, '--updating', current_executable], shell=False)

        # Beenden der aktuellen Anwendung
        sys.exit(0)

    except Exception as e:
        messagebox.showerror("Update fehlgeschlagen", f"Das Update konnte nicht installiert werden: {e}")
    finally:
        pass  # Wir können temp_dir hier nicht löschen, da die neue ausführbare Datei darin liegt
