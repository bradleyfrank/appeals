#!/usr/bin/env python

__author__ = 'Bradley Frank'

import magic
import os
import shutil
import sys
import urllib.request
import yaml
from urllib.error import HTTPError
from urllib.error import URLError


class PRDownloader:
    """
    Class for handling downloading, type checking, and saving documents from
    the MA Secretary of State website.
    """

    def __init__(self, prlog, prcfg, download_path, temp_directory):
        #
        # The current logger for the application.
        #
        self.prlog = prlog

        #
        # Temp directory to use for saving downloaded documents. From here,
        # the file will be moved to the download_path once it has been
        # converted to the proper format.
        #
        self.temp_directory = temp_directory

        #
        # The permanent directory to save downloads.
        #
        self.download_path = download_path

        #
        # A list of dictionaries of the documents being downloaded, comprised
        # of various attributes; allows for future referencing once the
        # download has completed. The format is as follows:
        #
        # downloads[document_id] = {
        #   filename: <filename>
        #   mimetype: <mimetype>
        #   extension: <extension>
        # }
        #
        self.downloads = []

        #
        # Keep track of the latest document downloaded. This value will be
        # used if the program was called using the --resume argument.
        #
        self.latest_document = None

        #
        # Log the successful creation of the class.
        #
        self.prlog.log('debug', 'Created new PRDownloader instance.') 

        #
        # Get the needed variables from the application config file that
        # was previously loaded and passed to this class.
        #
        self.base_url = prcfg['prdownloader']['base_url']
        self.mimetypes = prcfg['general']['mimetypes']

    def get_record(self, document_id):
        #
        # Pad the document number with zeros using zfill (e.g. 14 -> 00014).
        # The document_id needs to be a string first. This is how the website
        # numbers the documents for downloading.
        #
        document_id = str(document_id).zfill(5)

        #
        # Create the full download URL by appending the document_id to the
        # base URL of the MA Secretary of State Appeals website.
        #
        download_url = self.base_url + document_id

        #
        # Set a temporary filename for downloading the documents. This is so
        # the file can be analyzed before saving it permenantly.
        #
        tmpfile = os.path.join(self.temp_directory, document_id)

        #
        # Try to download the specified document. If problems are encountered
        # finding or downloading the document, log the error and skip to the
        # next document (if there is any remaining).
        #
        self.prlog.log('info', 'Downloading ' + download_url)
        try:
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
        self.prlog.log('debug', 'Writing to ' + tmpfile)
        try:
            with open(tmpfile, 'wb') as f:
                shutil.copyfileobj(response, f)
        except IOError as e:
            self.prlog.log('debug', e)
            sys.exit('Could not save to temp file ' + tmpfile)

        #
        # Determine the file extension by way of the file's mimetype.
        #
        mimetype = self.find_mimetype(tmpfile)

        if mimetype is not False:
            #
            # Match the discovered mimetype with allowable mimetypes to
            # determine the file extension.
            #
            extension = self.mimetypes[mimetype]
            self.prlog.log('debug', 'Determined extension to be ' + extension)
        else:
            return False

        #
        # With the extension determined, set the full path to the new
        # permenant file name.
        #
        filename = os.path.join(self.download_path,
                                document_id + '.' + extension)

        #
        # Move the temp file to the proper download location.
        #
        self.prlog.log('info', 'Moving temp file to ' + filename)
        try:
            shutil.move(tmpfile, filename)
        except IOError as e:
            self.prlog.log('debug', e)
            sys.exit('Could not move temp file to ' + filename)

        #
        # Update the latest document tracker.
        #
        self.latest_document = document_id

        #
        # Update the document dictionary.
        #
        self.downloads[document_id] = {
          'filename': filename,
          'mimetype': mimetype,
          'extension': extension,
        }

        #
        # The document was downloaded and saved successfully.
        #
        return True

    def find_mimetype(self, tmpfile):
        #
        # Determine the type of file downloaded. Usually it's either a
        # Word document, or a PDF.
        #
        mimetype = magic.from_file(tmpfile, mime=True)
        self.prlog.log('debug', 'Mimetype is ' + str(mimetype))

        if mimetype not in self.mimetypes:
            self.prlog.log('warning', 'Document is unexpected mimetype')
            return False

        return mimetype

    def get_filename(self, document_id):
        #
        # Returns the full path and filename of the saved document.
        #
        return self.downloads[document_id]['filename']

    def get_mimetype(self, document_id):
        #
        # Returns the mimetype of the saved document.
        #
        return self.downloads[document_id]['mimetype']

    def get_extension(self, document_id):
        #
        # Returns the file extension of the saved document.
        #
        return self.downloads[document_id]['extension']


if __name__ == '__main__':
    pass
