#!/usr/bin/env python
"""Analyzes documents to extract file types and metadata."""

__author__ = 'Bradley Frank'

import datetime
import lxml.etree
import magic
import re
import sys
import zipfile
from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError


class PRAnalyzer:
    """Analyzes documents to extract file types and metadata.

    :param prlog: A Logger instance.
    """

    def __init__(self, prlog):
        """Initialize PRAnalyzer class."""
        self.prlog = prlog

        #
        # File metadata for accessing and reading the document from disk/s3.
        #
        self.mimetype = None
        self.extension = None

        #
        # Document metadata for categorizing and searching.
        #
        self.createdBy = None
        self.createdDate = None
        self.modifiedDate = None
        self.title = None

        #
        # Log the successful creation of the class.
        #
        self.prlog.log('debug', 'Created new PRAnalyzer instance.')

    def find_mimetype(self, document):
        """Return the mimetype of the document."""
        #
        # Use the magic module to determine the mimetype.
        # https://github.com/ahupp/python-magic
        #
        magic_mimetype = magic.from_file(document, mime=True)
        self.prlog.log('debug', 'Mimetype is ' + str(magic_mimetype))
        return magic_mimetype

    def get_extension(self, document, mimetype, valid_mimetypes):
        """Determine file extension from the mimetype."""
        #
        # If not a valid file type, return nothing, ending here.
        #
        if mimetype not in valid_mimetypes:
            return None

        #
        # The mimetype is known and valid if it's defined in the global
        # config file. File extensions are stored as values in the
        # valid_mimetypes dictionary; to retrieve the extension, pass the
        # mimetype as the index. For example:
        #
        #   valid_mimetypes:
        #       'application/pdf': 'pdf'
        #
        # If self.mimetype is 'application/pdf', then the file extension is
        # 'pdf', referenced by self.valid_mimetypes[self.mimetype].
        #
        extension = valid_mimetypes[mimetype]
        self.prlog.log('debug', 'Determined extension to be ' +
                        self.extension)

        #
        # Return the file extension.
        #
        return extension

    def get_metadata(self):
        """Extract PDF and Word document metadata."""
        if self.extension == 'pdf':
            return self._get_metadata_pdf()
        elif self.extension == 'doc':
            return self._get_metadata_doc()
        else:
            return False

    def _get_metadata_pdf(self):
        with open(self.document, 'rb') as f:
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
        zf = zipfile.ZipFile(self.document)

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
        dc={ 'dc': 'http://purl.org/dc/elements/1.1/' }
        dcterms={ 'dcterms': 'http://purl.org/dc/terms/' }

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
