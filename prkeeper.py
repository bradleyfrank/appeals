#!/usr/bin/env python3

__author__ = 'Bradley Frank'

import argparse
import configparser
import logging
import magic
import mimetypes
import os
import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path
from urllib.error import HTTPError
from urllib.error import URLError

DOWNLOAD_PATH = '/srv/public_records/downloads/appeals'
STATUS_FILE = '/srv/public_records/status.log'
LOG_FILE = '/srv/public_records/logs/prkeeper.log'


class PublicRecordKeeper:

    BASE_URL = 'https://www.sec.state.ma.us' + \
               '/AppealsWeb/Download.aspx?DownloadPath='

    def __init__(self, prlog, temp_directory, download_path):
        self.prlog = prlog
        self.temp_directory = temp_directory
        self.download_path = download_path

        self.prlog.log('debug', 'Created new PublicRecordKeeper instance.')

    def get_records(self, file_ID):
        #
        # Pad the document number with zeros using zfill (e.g. 14 -> 00014).
        # The file_ID needs to be a string first. This is how the website
        # numbers the documents for downloading.
        #
        file_ID = str(file_ID).zfill(5)

        #
        # Create the full download URL by appending the file_ID to the
        # base URL of the MA Secretary of State Appeals website.
        #
        download_url = self.BASE_URL + file_ID

        #
        # Set a temporary filename for downloading the documents. This is so
        # the file can be analyzed before saving it permenantly.
        #
        tmpfile = os.path.join(self.temp_directory, file_ID)

        try:
            self.prlog.log('info', 'Downloading ' + download_url)
            response = urllib.request.urlopen(download_url)
        except HTTPError as e:
            self.prlog.log('warning', 'Could not download file ID ' + file_ID)
            self.prlog.log('debug', e.code)
            return False
        except URLError as e:
            self.prlog.log('warning', 'Could not download file ID ' + file_ID)
            self.prlog.log('debug', e.reason)
            return False

        try:
            with open(tmpfile, 'wb') as f:
                self.prlog.log('debug', 'Writing to ' + tmpfile)
                shutil.copyfileobj(response, f)
        except IOError as e:
            print(e)
            return False

        mime = magic.from_file(tmpfile, mime=True)
        self.prlog.log('debug', 'mimetype is ' + str(mime))

        if mime is None:
            return False
        elif mime == 'application/msword':
            ext = '.doc'
        elif mime == 'application/pdf':
            ext = '.pdf'
        else:
            ext = mimetypes.guess_extension(mime, True)

        self.prlog.log('debug', 'Used extension ' + ext)

        filename = os.path.join(self.download_path, file_ID + ext)

        self.prlog.log('info', 'Moving file to ' + filename)
        shutil.move(tmpfile, filename)

        return True


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
    #
    # Set available command-line arguments.
    #
    # --resume | --scope
    # Downloads can be expressed in an explicit range, or resumed from a prior
    # run of the program. Continuing is the default setting. The last download
    # is tracked in the status file. These settings are mutually exclusive.
    #
    # --debug
    # Prints all debug messages to the console.
    #
    parser = argparse.ArgumentParser(
        description='Downloads Massachusetts public record appeals.')

    download_method = parser.add_mutually_exclusive_group(required=True)
    download_method.add_argument('-r', '--resume', action='store_true',
                                 help='resumes downloading from a prior run')
    download_method.add_argument('-s', '--scope', type=int, nargs=2,
                                 help='a range of documents to download')

    parser.add_argument('-d', '--debug', action='store_true',
                        help='enables debug messages')

    #
    # Parse any passed command-line arguments.
    #
    args = parser.parse_args()

    if args.debug:
        prlog = PRLogger(LOG_FILE, log_to_console=True)
    else:
        prlog = PRLogger(LOG_FILE)

    if args.scope:
        if args.scope[1] < args.scope[0]:
            sys.exit('Start range cannot be greater than end range.')
        else:
            # Copy the arguments to a new variable.
            download_range = args.scope.copy()
            # Make the ending range inclusive.
            download_range[1] = download_range[1] + 1
            # Log the download method.
            prlog.log('info', 'Beginning new run with range ' + \
                      str(download_range[0]) + ' to ' + str(download_range[1]))
    else:
        prlog.log('info', 'Beginning new run resuming from ')

    #
    # Ensure the download directory exists.
    #
    if not os.path.isdir(DOWNLOAD_PATH):
        os.makedirs(DOWNLOAD_PATH, exist_ok=True)

    #
    # Instantiate the main class with provided settings. This passes a
    # temporary system directory to use as scratch space.
    #
    prkeeper = PublicRecordKeeper(prlog, tempfile.mkdtemp(), DOWNLOAD_PATH)

    #
    # Loop through the specified document range to download documents.
    #
    for document in range(download_range[0], download_range[1]):
        prkeeper.get_records(document)

    prlog.log('debug', 'Ending current run.\n')