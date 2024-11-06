# minilink/utils/settings.py

import os
import json
from appdirs import user_config_dir

class SettingsManager:
    def __init__(self, app_name="minilink", app_author="Elias Müller"):
        self.app_name = app_name
        self.app_author = app_author
        self.config_dir = user_config_dir(self.app_name, self.app_author)
        self.config_file = os.path.join(self.config_dir, 'settings.json')
        self.settings = self.load_settings()

    def load_settings(self):
        if not os.path.exists(self.config_file):
            return {}
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            return settings
        except Exception as e:
            print(f"Fehler beim Laden der Einstellungen: {e}")
            return {}

    def save_setting(self, name, value):
        self.settings[name] = value
        self.save_settings()

    def save_settings(self):
        os.makedirs(self.config_dir, exist_ok=True)
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Fehler beim Speichern der Einstellungen: {e}")

    def get(self, name, default=None):
        return self.settings.get(name, default)
