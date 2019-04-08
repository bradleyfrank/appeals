#!/usr/bin/env python

__author__ = 'Bradley Frank'

import datetime
import lxml.etree
import re
import sys
import zipfile
from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError


class PRAnalyzer:

    def __init__(self, prlog, filename, mimetype, extension):
        #
        # The current logger for the application.
        #
        self.prlog = prlog

        #
        # Today's date for comparison to document creation date.
        #
        self.today = datetime.datetime.now()

        #
        # File metadata for accessing and reading the document from disk/s3.
        #
        self.filename = filename
        self.mimetype = mimetype
        self.extension = extension

        #
        # Document metadata to be filled in later.
        #
        self.createdBy = None
        self.createdDate = None
        self.modifiedDate = None
        self.title = None

    def get_metadata(self):
        """Extract PDF and Word document metadata.
        """

        if self.extension == 'pdf':
            return self._get_metadata_pdf()
        elif self.extension == 'doc':
            return self._get_metadata_doc()
        else:
            return False

    def _get_metadata_pdf(self):
        with open(self.filename, 'rb') as f:
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

        self.createdBy = creator
        self.createdDate = self._normalize_date(creation_date)
        self.modifiedDate = modified
        self.title = title

        return True

    def _get_metadata_doc(self):
        #
        # A docx file is a compressed set of files that describe the Word
        # document, plus the document itself. To retrieve the metadata, the
        # docx needs to be extracted into its component parts.
        #
        zf = zipfile.ZipFile(self.filename)

        #
        # Once extracted, the file '/docProps/core.xml' contains the metadata
        # of the Word document, in XML format. Here, the XML data is loaded.
        #
        doc = lxml.etree.fromstring(zf.read('docProps/core.xml'))

        #
        # The XML namespaces needs to be defined in order to parse the data.
        # Usually this can be find in the XML file itself, but here it needs
        # to be manually set.
        #
        dc={'dc': 'http://purl.org/dc/elements/1.1/'}
        dcterms={'dcterms': 'http://purl.org/dc/terms/'}

        #
        # Extract the required metadata using the proper namespaces from above.
        #
        created = doc.xpath('//dcterms:created', namespaces=dcterms)[0].text
        modified = doc.xpath('//dcterms:modified', namespaces=dcterms)[0].text
        creator = doc.xpath('//dc:creator', namespaces=dc)[0].text
        title = doc.xpath('//dc:title', namespaces=dc)[0].text

        self.createdBy = creator
        self.createdDate = self._normalize_date(created)
        self.modifiedDate = self._normalize_date(modified)
        self.title = title

    def _normalize_date(self, formatted_date):
        pass


if __name__ == '__main__':
    pass
