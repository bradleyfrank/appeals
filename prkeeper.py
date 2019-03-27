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
from urllib.error import HTTPError
from urllib.error import URLError


class PublicRecordKeeper:

    BASE_URL = 'https://www.sec.state.ma.us' + \
               '/AppealsWeb/Download.aspx?DownloadPath='

    def __init__(self, prlog, temp_directory, download_path):
        self.prlog = prlog
        self.temp_directory = temp_directory
        self.download_path = download_path

        if not os.path.isdir(self.download_path):
            os.makedirs(self.download_path, exist_ok=True)

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
                self.prlog.log('info', 'Writing to ' + tmpfile)
                shutil.copyfileobj(response, f)
        except IOError as e:
            print(e)
            return False

        mime = magic.from_file(tmpfile, mime=True)
        self.prlog.log('info', 'mimetype is ' + str(mime))

        if mime is None:
            return False
        elif mime == 'application/msword':
            ext = '.doc'
        elif mime == 'application/pdf':
            ext = '.pdf'
        else:
            ext = mimetypes.guess_extension(mime, True)

        self.prlog.log('info', 'Used extension ' + ext)

        filename = os.path.join(self.download_path, file_ID + ext)

        self.prlog.log('info', 'Moving file to ' + filename)
        shutil.move(tmpfile, filename)

        return True


class PRLogger:

    def __init__(self, debug=False, log_to_console=False, log_to_stdout=False):
        self.logger = logging.getLogger('prkeeper')

        _log_format = '[%(asctime)s] [%(levelname)8s] %(message)s'
        self.log_format = logging.Formatter(_log_format, '%H:%M:%S')

        if not debug:
            self.log_level = 0
        else:
            self.log_level = 10

        self.logger.setLevel(self.log_level)

        if log_to_console or debug:
            self.log_to_console()

        if log_to_stdout:
            self.log_to_file()

    def log_to_console(self):
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(self.log_level)
        ch.setFormatter(self.log_format)
        self.logger.addHandler(ch)

    def log_to_file(self):
        fh = logging.FileHandler('/var/log/prkeeper.log')
        fh.setLevel(self.log_level)
        fh.setFormatter(self.log_format)
        self.logger.addHandler(fh)

    def log(self, lvl, msg):
        level = logging.getLevelName(lvl.upper())
        self.logger.log(level, msg)


if __name__ == '__main__':
    #
    # Get the current working directory of this script.
    #
    # The join() call prepends the current working directory, but the
    # documentation says that if some path is absolute, all other paths left
    # of it are dropped. Therefore, getcwd() is dropped when dirname(__file__)
    # returns an absolute path. The realpath call resolves symbolic links if
    # any are found.
    #
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))

    #
    # Read the config file and parse out the settings, saving them as
    # variables.
    #
    config_file = os.path.join(__location__, 'prkeeper.conf')

    conf = configparser.ConfigParser()
    conf.read(config_file)

    download_path = conf['downloads']['download_path']
    download_range_start = int(conf['downloads']['download_range_start'])
    download_range_end = int(conf['downloads']['download_range_end'])

    #
    # Set available command-line arguments.
    #
    parser = argparse.ArgumentParser(
        description='Wrapper for reposync and createrepo.')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='enables debug messages')

    #
    # Parse any passed command-line arguments.
    #
    args = parser.parse_args()

    if args.debug:
        prlog = PRLogger(debug=True)
    else:
        prlog = PRLogger(debug=False)

    #
    # Instantiate the main class with provided settings. This passes a
    # temporary system directory to use as scratch space.
    #
    prkeeper = PublicRecordKeeper(prlog, tempfile.mkdtemp(), download_path)

    #
    # Loop through the specified document range to download documents.
    #
    for document in range(download_range_start, download_range_end):
        prkeeper.get_records(document)
