# minilink/server/http_server.py

import http.server
import socketserver
import threading
import os
import json
import logging

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Angepasster HTTP-Request-Handler mit benutzerdefiniertem Web-Root."""

    def __init__(self, *args, web_root=None, directory_listing=True, **kwargs):
        self.web_root = web_root
        self.directory_listing = directory_listing
        super().__init__(*args, directory=self.web_root, **kwargs)

    def log_message(self, format, *args):
        """Protokolliere Anfragen."""
        logging.info("%s - - [%s] %s\n" % (self.client_address[0],
                                           self.log_date_time_string(),
                                           format % args))

    def list_directory(self, path):
        """Steuere die Verzeichnisauflistung basierend auf der Einstellung."""
        if not self.directory_listing:
            self.send_error(403, "Verzeichnisauflistung ist deaktiviert")
            return None
        return super().list_directory(path)

    def do_GET(self):
        """Behandle GET-Anfragen mit benutzerdefinierter Logik."""
        if self.path in ["/templates", "/templates/"]:
            templates_dir = os.path.join(self.web_root, "templates")
            if os.path.isdir(templates_dir):
                json_files = [f for f in os.listdir(templates_dir) if f.endswith(".json")]
                json_data = json.dumps(json_files)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json_data.encode("utf-8"))
            else:
                self.send_error(404, "Templates-Verzeichnis nicht gefunden")
        elif self.path.startswith("/templates/"):
            file_name = os.path.basename(self.path)
            file_path = os.path.join(self.web_root, "templates", file_name)
            if os.path.isfile(file_path) and file_name.endswith(".json"):
                with open(file_path, "r", encoding="utf-8") as file:
                    file_content = file.read()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(file_content.encode("utf-8"))
            else:
                self.send_error(404, "Datei nicht gefunden")
        else:
            super().do_GET()

class ServerManager:
    """Manager-Klasse zur Steuerung des HTTP-Servers."""

    def __init__(self, web_root, port, timeout, directory_listing):
        self.web_root = web_root
        self.port = port
        self.timeout = timeout
        self.directory_listing = directory_listing
        self.server = None
        self.thread = None

    def start(self):
        handler = lambda *args, **kwargs: CustomHTTPRequestHandler(
            *args,
            web_root=self.web_root,
            directory_listing=self.directory_listing,
            **kwargs
        )
        self.server = socketserver.TCPServer(("", self.port), handler)
        self.server.timeout = self.timeout
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join()
            self.server = None
            self.thread = None

    def restart(self, web_root=None, port=None, timeout=None, directory_listing=None):
        self.stop()
        if web_root is not None:
            self.web_root = web_root
        if port is not None:
            self.port = port
        if timeout is not None:
            self.timeout = timeout
        if directory_listing is not None:
            self.directory_listing = directory_listing
        self.start()
