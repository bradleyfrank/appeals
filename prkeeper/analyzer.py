#!/usr/bin/env python3.4

__author__ = 'Bradley Frank'

import datetime
from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError


class PRAnalyzer:

    def __init__(self, prlog):
        #
        # The current logger for the application.
        #
        self.prlog = prlog

        #
        # Today's date for comparison to document creation date.
        #
        self.today = datetime.datetime.now()

        #
        # The creation date of the document is used to inform the program
        # to continue or stop downloading further documents (since in theory
        # there wouldn't be documents with creation dates in the future), even
        # if the program hasn't reached the end of a specified range given by
        # the user. The first step is to extract the creation date.
        #
        date = get_date(extension, tmpfile)

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
