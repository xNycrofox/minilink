# minilink/utils/logger.py

import logging

class Logger:
    def __init__(self):
        self.logger = logging.getLogger('minilink')
        if not self.logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.setLevel(logging.INFO)
            self.logger.addHandler(handler)

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)
