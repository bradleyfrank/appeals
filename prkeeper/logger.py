#!/usr/bin/env python3.4

__author__ = 'Bradley Frank'

import logging


class PRLogger:
    def __init__(self, logfile, log_to_console=False, log_to_file=True):
        self.logger = logging.getLogger('prkeeper')

        self.log_format = logging.Formatter(
            '[%(asctime)s] [%(levelname)8s] %(message)s',
            '%H:%M:%S')

        self.log_level = 10
        self.logger.setLevel(self.log_level)

        if log_to_console:
            self.log_to_console()

        if log_to_file:
            log_dir, _ = os.path.split(logfile)

            if not os.path.isdir(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            if not os.path.isfile(LOG_FILE):
                Path(LOG_FILE).touch()

            self.log_to_file(logfile)

    def log_to_console(self):
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(self.log_level)
        ch.setFormatter(self.log_format)
        self.logger.addHandler(ch)

    def log_to_file(self, logfile):
        fh = logging.FileHandler(logfile)
        fh.setLevel(self.log_level)
        fh.setFormatter(self.log_format)
        self.logger.addHandler(fh)

    def log(self, lvl, msg):
        level = logging.getLevelName(lvl.upper())
        self.logger.log(level, msg)


if __name__ == '__main__':
    pass
