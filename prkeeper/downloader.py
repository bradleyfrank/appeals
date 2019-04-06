#!/usr/bin/env python3.4

__author__ = 'Bradley Frank'

import datetime
import magic
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


class PRDownloader:
    """
    Class for handling downloading, type checking, and saving documents from
    the MA Secretary of State website.
    """

    BASE_URL = 'https://www.sec.state.ma.us' + \
               '/AppealsWeb/Download.aspx?DownloadPath='

    def __init__(self, prlog, download_path):
        # The current logger.
        self.prlog = prlog
        # A temporary directory to use as scratch space to save downloads.
        self.temp_directory = tempfile.mkdtemp()
        # The permanent directory to save downloads.
        self.download_path = download_path
        # Today's date for comparison to document creation date.
        self.today = datetime.datetime.now()
        # Latest document successfully downloaded.
        self.latest_document = None

        self.prlog.log('debug', 'Created new PRDownloader instance.')

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
        # Determine the type of file downloaded. Ususally it's either a
        # Word document, or a PDF.
        #
        mime = magic.from_file(tmpfile, mime=True)
        self.prlog.log('debug', 'Mimetype is ' + str(mime))

        if mime == 'application/msword':
            extension = 'doc'
        elif mime == 'application/pdf':
            extension = 'pdf'
        else:
            return False

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
        self.prlog.log('info', 'Moving temp file to ' + filename)
        try:
            shutil.move(tmpfile, filename)
        except IOError as e:
            self.prlog.log('debug', e)
            sys.exit('Could not move temp file to ' + filename)

        #
        # Keep track of the latest document downloaded. This value will be
        # used if the program was called using the --resume argument.
        #
        self.latest_document = file_ID

        return True

    def get_date(self, file_type, tmpfile):
        """Extract a date from PDFs and Word documents metadata.

        Args:
            file_type (str): The file type
            tmpfile (str): The file path

        Returns:
            created_date (datetime): The file created date
        """

        def get_date_pdf(tmpfile):
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
                pdf_creation_date = metadata['/CreationDate']

            match = re.search(r'\d+', pdf_creation_date)

            creation_date = datetime.datetime.strptime(
                match.group(), '%Y%m%d%H%M%S'
            )

            return creation_date

        def get_date_doc(tmpfile):
            return None

        if file_type == 'pdf':
            return get_date_pdf(tmpfile)
        elif file_type == 'doc':
            return get_date_doc(tmpfile)
        else:
            return False


if __name__ == '__main__':
    pass
