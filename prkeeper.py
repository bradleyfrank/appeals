#!/usr/bin/env python3

__author__ = 'Bradley Frank'

import argparse
import datetime
import logging
import magic
import mimetypes
import os
import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path
from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError
from urllib.error import HTTPError
from urllib.error import URLError

#
# General script variables; see __main__ function below.
#
# DOWNLOAD_PATH: save location for all downloaded documents
# STATUS_FILE: tracks latest document downloaded
# LOG_FILE: application-wide log file
#
DOWNLOAD_PATH = '/srv/public_records/downloads/appeals'
STATUS_FILE = '/srv/public_records/status.log'
LOG_FILE = '/srv/public_records/logs/prkeeper.log'


class PublicRecordKeeper:
    """
    Class for handling downloading, type checking, and saving documents from
    the MA Secretary of State website.
    """

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

        #
        # Try to download the specified document. If problems are encountered
        # finding or downloading the document, log the error and skip to the
        # next document (if there is any remaining).
        #
        try:
            self.prlog.log('info', 'Downloading ' + download_url)
            response = urllib.request.urlopen(download_url)
        except HTTPError as e:
            self.prlog.log('warning', 'There was a problem retrieving \
                           the file')
            self.prlog.log('debug', e.code)
            return False
        except URLError as e:
            self.prlog.log('warning', 'There was a problem finding the file')
            self.prlog.log('debug', e.reason)
            return False

        #
        # Save the data retrieved from the website to a temporary file. This
        # allows analyzing the file before saving it permanently.
        #
        try:
            with open(tmpfile, 'wb') as f:
                self.prlog.log('debug', 'Writing to ' + tmpfile)
                shutil.copyfileobj(response, f)
        except IOError as e:
            self.prlog.log('debug', e)
            sys.exit('Could not save to temp file ' + tmpfile)

        #
        # Determine the type of file downloaded. Ususally it's either a Word
        # document, or a PDF. If neither, try to automatically determine the
        # file extension from the mimetype. If the mimetype cannot be
        # determined, there's a problem with the file (could be corrupt) and it
        # needs to be investigated.
        #
        mime = magic.from_file(tmpfile, mime=True)
        self.prlog.log('debug', 'mimetype is ' + str(mime))

        if mime is None:
            extension = 'unknown'
        elif mime == 'application/msword':
            extension = 'doc'
        elif mime == 'application/pdf':
            extension = 'pdf'
        else:
            #
            # The function guess_extension returns a "." prefix so remove it
            # with [1:]; this makes it easier to reference the extension, and
            # the dot will be re-added manually later on.
            #
            extension = mimetypes.guess_extension(mime, True)[1:]

        self.prlog.log('debug', 'Determined extension to be ' + extension)

        #
        # The creation date of the document is used to inform the program
        # to continue or stop downloading further documents (since in theory
        # there wouldn't be documents with creation dates in the future), even
        # if the program hasn't reached the end of a specified range given by
        # the user. The first step is to extract the creation date.
        #
        date = get_date(extension, tmpfile)

        #
        # With the extension determined, set the full path to the new
        # permenant file name. The dot before the extension is re-added here.
        #
        filename = os.path.join(self.download_path, file_ID + '.' + extension)

        #
        # Move the temp file into proper download location.
        #
        self.prlog.log('info', 'Moving file to ' + filename)
        shutil.move(tmpfile, filename)

        return True

    def get_date(self, file_type, tmpfile):
        if file_type == 'pdf':
            with open(tmpfile, 'rb') as f:
                try:
                    pdf = PdfFileReader(f)
                except PdfReadError as e:
                    self.prlog.log('debug', e)
                    sys.exit('Could not open PDF to read metadata.')

                metadata = pdf.getDocumentInfo()
                self.prlog.log('debug', metadata)

            if '/CreationDate' not in metadata:
                self.prlog.log('warning', 'Creation date not found')
                return None
            else:
                creation_date = metadata['/CreationDate']

            match = re.search('\d+', creation_date)
            fulldate = datetime.datetime.strptime(
                match.group(), '%Y%m%d%H%M%S'
            )

            return fulldate.strftime('%Y-%m-%d')


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
    arguments = argparse.ArgumentParser(
        description='Downloads Massachusetts public record appeals.')

    #
    # --debug
    # Prints all debug messages to the console.
    #
    arguments.add_argument('-d', '--debug', action='store_true',
                           help='enables debug messages')

    #
    # --resume | --scope
    # Downloads can be expressed in an explicit range, or resumed from a prior
    # run of the program. Continuing is the default setting. The last download
    # is tracked in the status file. These settings are mutually exclusive.
    #
    download_method = arguments.add_mutually_exclusive_group(required=True)
    download_method.add_argument('-r', '--resume', action='store_true',
                                 help='resumes downloading from a prior run')
    download_method.add_argument('-s', '--scope', type=int, nargs=2,
                                 help='download documents between start and \
                                 end values (inclusive); set end value to 0 \
                                 to download all available documents after \
                                 start value')

    #
    # --s3
    # Saves documents to an AWS s3 bucket. By default the documents save to
    # disk, but s3 can also be used. Credentials for AWS should be entered
    # into the credentials.env file found in this Git repo.
    #
    arguments.add_argument('--s3', action='store_true',
                           help='saves downloads to aws s3 bucket')

    #
    # Parses all the arguments passed to the script.
    #
    args = arguments.parse_args()

    #
    # Sets logging for the application: adds additional conole output if
    # the debug argument is passed, otherwise just logs to file by default.
    #
    if args.debug:
        prlog = PRLogger(LOG_FILE, log_to_console=True)
    else:
        prlog = PRLogger(LOG_FILE)

    #
    # One of two download methods must be given to begin downloading: (a) a
    # range of documents to download, or (b) resume downloading from where
    # last left off.
    #
    if args.scope:
        if args.scope[1] < args.scope[0] and args.scope[1] != 0:
            sys.exit('Start range cannot be greater than end range.')
        else:
            # Copy the arguments to a new stand-alone variable.
            download_range = args.scope.copy()
            # Make the ending range inclusive, as the user would expect.
            download_range[1] = download_range[1] + 1
            # Log the download method.
            prlog.log('info', 'Beginning new run with range ' +
                      str(download_range[0]) + ' to ' + str(download_range[1]))
    else:
        prlog.log('info', 'Resuming downloads')

    #
    # If s3 was selected, setup the bucket if one does not exist already.
    # Otherwise, ensure the download directory exists on disk.
    #
    if args.s3:
        pass
    elif not os.path.isdir(DOWNLOAD_PATH):
        os.makedirs(DOWNLOAD_PATH, exist_ok=True)

    #
    # Instantiate the main class with provided settings. This passes a
    # temporary directory to use as scratch space to save downloads.
    #
    prkeeper = PublicRecordKeeper(prlog, tempfile.mkdtemp(), DOWNLOAD_PATH)

    #
    # Loop through the specified range to download documents.
    #
    for document in range(download_range[0], download_range[1]):
        prkeeper.get_records(document)

    prlog.log('debug', 'Ending current run\n')
