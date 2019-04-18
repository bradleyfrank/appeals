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

    def __init__(self, prlog, document):
        #
        # The current logger for the application.
        #
        self.prlog = prlog

        #
        # The document to be analzyed.
        #
        self.document = document

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

        #
        # Log the successful creation of the class.
        #
        self.prlog.log('debug', 'Created new PRAnalyzer instance.')

    def find_mimetype(self):
        #
        # Use the magic module to determine the mimetype.
        # https://github.com/ahupp/python-magic
        #
        mimetype = magic.from_file(self.document, mime=True)
        self.prlog.log('debug', 'Mimetype is ' + str(mimetype))

        #
        # The old binary MS Word documents (.doc) are difficult to read and
        # parse, so they need to be converted to the newer XML format (.docx)
        # which is handled by the command line version of LibreOffice. This has
        # the added benefit of retaining all the original metadata.
        #
        if mimetype == 'application/msword':
            self.document = self.convert_doc_to_docx(self.document,
                                                    self.document_id)

            #
            # If the file conversion failed for any reason, return the null
            # result. The metadata cannot be trusted if LibreOffice was unable
            # to read the file at all.
            #
            if self.document is None:
                return None

            #
            # Otherwise if successful, now re-check the metadata of the 
            # newly converted docx file.
            #
            return self.get_metadata()
        #
        # The mimetype was found and is supported.
        #
        elif mimetype in self.valid_mimetypes:
            #
            # Match the discovered mimetype with allowable mimetypes to
            # determine the file extension.
            #
            self.extension = self.valid_mimetypes[mimetype]
            self.prlog.log('debug', 'Determined extension to be ' +
                           self.extension)
            return mimetype
        #
        # If the mimetype is unsupported, or couldn't be determined, end here,
        # setting the document's attributes to null. It's a good indication
        # there existed no file with this ID and the website returned an html
        # document, which represents the site redirecting back to the main
        # search page.
        #
        else:
            self.prlog.log('warning', 'Document is unexpected/unsupported \
                           mimetype')
            return None

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
