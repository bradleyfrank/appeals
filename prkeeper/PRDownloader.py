#!/usr/bin/env python

__author__ = 'Bradley Frank'

import os
import shutil
import subprocess
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

    def __init__(self, prlog, prcfg):
        #
        # The current logger for the application.
        #
        self.prlog = prlog

        #
        # Get the needed variables from the application config file.
        #
        self.base_url = prcfg['prdownloader']['base_url']
        self.download_path_final = prcfg['prdownloader']['download_path_final']
        self.download_path_raw = prcfg['prdownloader']['download_path_raw']

        #
        # Log the successful creation of the class.
        #
        self.prlog.log('debug', 'Created new PRDownloader instance.')


    def download_document(self, document_id):
        #
        # The ID of the appeal document to download.
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
        rawfile = os.path.join(self.download_path_raw, document_id)

        #
        # Try to download the specified document. If problems are encountered
        # finding or downloading the document, log the error and skip to the
        # next document (if there is any remaining).
        #
        self.prlog.log('info', 'Downloading ' + download_url)
        try:
            response = urllib.request.urlopen(download_url)
        except HTTPError as e:
            self.prlog.log('warning', 'There was a problem retrieving the file')
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
        self.prlog.log('info', 'Writing to ' + rawfile)

        try:
            f = open(rawfile, 'wb')
            try:
                shutil.copyfileobj(response, f)
            except IOError as e:
                self.prlog.log('debug', e)
                sys.exit('Could not save to temp file ' + rawfile)
            finally:
                f.close()
        except OSError as e:
            self.prlog.log('debug', e)
            sys.exit('Could not open the temp file ' + rawfile)

        return rawfile

    def save_final_document(self, document_id):
        rawfile = os.path.join(self.download_path_raw, document_id)
        filename = os.path.join(self.download_path_final, document_id)

        #
        # Ensure the raw document exists before moving it.
        #
        if not os.path.isfile(rawfile):
            return None

        #
        # Move the raw file to the proper download location.
        #
        self.prlog.log('info', 'Moving raw file to ' + filename)
        try:
            shutil.move(rawfile, filename)
        except IOError as e:
            self.prlog.log('debug', e)
            sys.exit('Could not move raw file to ' + filename)


if __name__ == '__main__':
    pass
