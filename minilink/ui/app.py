# minilink/ui/app.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import webbrowser
import os
import sys
import subprocess
import logging

from minilink.server.http_server import ServerManager
from minilink.utils.settings import SettingsManager
from minilink.utils.logger import Logger
from minilink.utils.updater import check_for_update

class MinilinkApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Minilink")
        self.root.geometry("800x600")
        self.settings = SettingsManager()
        self.logger = Logger()
        self.setup_variables()
        self.create_ui()
        self.server_manager = None
        self.connections_queue = queue.Queue()
        self.update_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        self.progress_window = None
        threading.Thread(target=self.check_for_update_thread).start()
        self.process_update_queue()


    def check_for_update_thread(self):
        check_for_update(self.update_queue, self.progress_queue)


    def process_update_queue(self):
        try:
            while True:
                message = self.update_queue.get_nowait()
                self.status_label.config(text=f"© 2024 Elias Müller | {message}")
        except queue.Empty:
            pass
        self.root.after(100, self.process_update_queue)

    def show_progress_window(self):
        """Erstellt ein neues Fenster mit einem Fortschrittsbalken."""
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("Update wird heruntergeladen...")
        self.progress_window.geometry("300x100")
        self.progress_label = tk.Label(self.progress_window, text="Download Fortschritt")
        self.progress_label.pack(pady=10)
        self.progress_bar = ttk.Progressbar(self.progress_window, orient='horizontal', length=250, mode='determinate')
        self.progress_bar.pack(pady=10)
        self.update_progress_bar()

    def update_progress_bar(self):
        try:
            while True:
                progress = self.progress_queue.get_nowait()
                self.progress_bar['value'] = progress
                self.progress_window.update_idletasks()
                if progress >= 100:
                    self.progress_window.destroy()
                    break
        except queue.Empty:
            pass
        self.root.after(100, self.update_progress_bar)

    def setup_variables(self):
        self.web_root = self.settings.get("web_root", os.getcwd())
        self.port = self.settings.get("port", 8000)
        self.timeout = self.settings.get("timeout", 60)
        self.directory_listing = self.settings.get("directory_listing", True)
        self.is_running = False

    def create_ui(self):
        # Tabs erstellen
        self.tab_control = ttk.Notebook(self.root)

        # Dashboard Tab
        self.dashboard_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.dashboard_tab, text="Dashboard")

        # Logs Tab
        self.logs_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.logs_tab, text="Logs")

        # Verbindungen Tab
        self.connections_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.connections_tab, text="Verbindungen")

        # Einstellungen Tab
        self.settings_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.settings_tab, text="Einstellungen")

        self.tab_control.pack(expand=1, fill="both")

        # UI-Komponenten für jeden Tab erstellen
        self.create_dashboard_ui()
        self.create_logs_ui()
        self.create_connections_ui()
        self.create_settings_ui()

        # Statusleiste oder Copyright
        self.status_label = tk.Label(
            self.root, text="© 2024 Elias Müller | Prüfe auf Updates...", fg="gray", font=("Arial", 10)
        )
        self.status_label.pack(side="bottom", pady=5)


    def create_dashboard_ui(self):
        """Erstelle die Dashboard-UI-Komponenten."""
        padding = 10

        # Web Root
        self.web_root_label = tk.Label(
            self.dashboard_tab, text=f"Web Root: {self.web_root}", wraplength=600, justify="left"
        )
        self.web_root_label.pack(pady=(padding, 5))

        self.change_dir_button = ttk.Button(
            self.dashboard_tab, text="Web Root ändern", command=self.select_directory
        )
        self.change_dir_button.pack(pady=5)

        self.open_dir_button = ttk.Button(
            self.dashboard_tab, text="Web Root im Explorer öffnen", command=self.open_directory
        )
        self.open_dir_button.pack(pady=5)

        # Port
        self.port_label = tk.Label(self.dashboard_tab, text=f"Port: {self.port}")
        self.port_label.pack(pady=(padding, 5))

        self.change_port_button = ttk.Button(
            self.dashboard_tab, text="Port ändern", command=self.change_port
        )
        self.change_port_button.pack(pady=5)

        # Server Start/Stop
        self.toggle_button = ttk.Button(
            self.dashboard_tab, text="Server starten", command=self.toggle_server, width=20
        )
        self.toggle_button.pack(pady=5)

        # Server Status
        self.server_status_label = tk.Label(self.dashboard_tab, text="Status: Gestoppt", fg="red")
        self.server_status_label.pack(pady=(padding, 5))

        # Server Adresse
        self.address_label = tk.Label(
            self.dashboard_tab, text="", fg="blue", cursor="hand2"
        )
        self.address_label.pack(pady=5)
        self.address_label.bind("<Button-1>", self.open_link)

    def create_logs_ui(self):
        """Erstelle die Logs-UI-Komponenten."""
        self.logs_text = scrolledtext.ScrolledText(
            self.logs_tab, wrap="word", height=10, state="disabled"
        )
        self.logs_text.pack(expand=True, fill="both")

        # Logger starten
        self.setup_logging()

    def create_connections_ui(self):
        """Erstelle die Verbindungen-UI-Komponenten."""
        self.connections_label = tk.Label(self.connections_tab, text="Verbindungen")
        self.connections_label.pack(pady=10)

        self.connections_listbox = tk.Listbox(self.connections_tab)
        self.connections_listbox.pack(expand=True, fill="both")

        # Verbindungen aktualisieren
        self.update_connections_list()

    def create_settings_ui(self):
        """Erstelle die Einstellungen-UI-Komponenten."""
        padding = 10

        # Timeout
        timeout_label = tk.Label(self.settings_tab, text="Verbindungstimeout (Sekunden)")
        timeout_label.pack(pady=(padding, 5))
        self.timeout_entry = ttk.Entry(self.settings_tab)
        self.timeout_entry.insert(0, str(self.timeout))
        self.timeout_entry.pack(pady=5)

        # Verzeichnisauflistung
        self.directory_listing_var = tk.BooleanVar(value=self.directory_listing)
        dir_listing_checkbox = ttk.Checkbutton(
            self.settings_tab,
            text="Verzeichnisauflistung aktivieren",
            variable=self.directory_listing_var
        )
        dir_listing_checkbox.pack(pady=5)

        # Einstellungen speichern
        save_button = ttk.Button(self.settings_tab, text="Speichern", command=self.save_settings)
        save_button.pack(pady=10)

    def save_settings(self):
        """Einstellungen speichern."""
        self.timeout = int(self.timeout_entry.get())
        self.directory_listing = self.directory_listing_var.get()

        self.settings.save_setting('timeout', self.timeout)
        self.settings.save_setting('directory_listing', self.directory_listing)

        messagebox.showinfo("Einstellungen", "Einstellungen wurden gespeichert.")

    def setup_logging(self):
        """Konfiguriere das Logging."""
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.log_queue = queue.Queue()

        def log_writer():
            while True:
                try:
                    log_entry = self.log_queue.get(timeout=1)
                    self.logs_text.config(state="normal")
                    self.logs_text.insert(tk.END, log_entry)
                    self.logs_text.config(state="disabled")
                    self.logs_text.see(tk.END)
                except queue.Empty:
                    pass

        log_thread = threading.Thread(target=log_writer)
        log_thread.daemon = True
        log_thread.start()

    def select_directory(self):
        """Web-Root-Verzeichnis auswählen."""
        web_root = filedialog.askdirectory(
            initialdir=self.web_root, title="Wähle das Web Root-Verzeichnis"
        )
        if web_root:
            self.web_root = web_root
            self.settings.save_setting('web_root', web_root)
            self.web_root_label.config(text=f"Web Root: {self.web_root}")
            if self.is_running:
                self.restart_server()

    def open_directory(self):
        """Öffne das Web-Root-Verzeichnis im Explorer."""
        if os.path.isdir(self.web_root):
            if sys.platform == 'win32':
                os.startfile(self.web_root)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', self.web_root])
            else:
                subprocess.Popen(['xdg-open', self.web_root])

    def change_port(self):
        """Port ändern."""
        new_port = tk.simpledialog.askinteger(
            "Port ändern",
            "Gib einen neuen Port ein:",
            initialvalue=self.port,
            minvalue=1,
            maxvalue=65535
        )
        if new_port:
            self.port = new_port
            self.settings.save_setting('port', new_port)
            self.port_label.config(text=f"Port: {self.port}")
            if self.is_running:
                self.restart_server()

    def toggle_server(self):
        """Server starten oder stoppen."""
        if not self.is_running:
            self.start_server()
        else:
            self.stop_server()

    def start_server(self):
        """Webserver starten."""
        self.server_manager = ServerManager(
            web_root=self.web_root,
            port=self.port,
            timeout=self.timeout,
            directory_listing=self.directory_listing
        )
        try:
            self.server_manager.start()
            self.is_running = True
            self.toggle_button.config(text="Server stoppen")
            self.server_status_label.config(text="Status: Laufend", fg="green")
            self.update_address_label()
            self.logger.info(f"Server gestartet auf http://localhost:{self.port}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Kann den Server nicht starten: {e}")

    def stop_server(self):
        """Webserver stoppen."""
        if self.server_manager:
            self.server_manager.stop()
            self.is_running = False
            self.toggle_button.config(text="Server starten")
            self.server_status_label.config(text="Status: Gestoppt", fg="red")
            self.address_label.config(text="")
            self.logger.info("Server gestoppt.")

    def restart_server(self):
        """Webserver neu starten."""
        self.stop_server()
        self.start_server()

    def update_address_label(self):
        """Aktualisiere die Anzeige der Serveradresse."""
        address = f"http://localhost:{self.port}"
        self.address_label.config(text=f"Aufrufbar unter: {address}")
        self.address = address

    def open_link(self, event):
        """Öffne die Serveradresse im Browser."""
        if self.is_running:
            webbrowser.open(self.address)

    def update_connections_list(self):
        """Aktualisiere die Verbindungen."""
        # Implementiere hier die Logik, um die Verbindungen zu aktualisieren
        self.root.after(1000, self.update_connections_list)

    def run(self):
        """Starte die Tkinter-Hauptschleife."""
        self.root.mainloop()
