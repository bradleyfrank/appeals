#!/usr/bin/env python

__author__ = 'Bradley Frank'

import magic
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

    def __init__(self, prlog, prcfg, document_id,
                 temp_directory, download_path):
        #
        # The current logger for the application.
        #
        self.prlog = prlog

        #
        # Get the needed variables from the application config file that
        # was previously loaded and passed here.
        #
        self.base_url = prcfg['prdownloader']['base_url']
        self.mimetypes = prcfg['general']['mimetypes']

        #
        # The ID of the appeal document to download.
        # Pad the document number with zeros using zfill (e.g. 14 -> 00014).
        # The document_id needs to be a string first. This is how the website
        # numbers the documents for downloading.
        #
        self.document_id = str(document_id).zfill(5)

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
        # Initialize the document metadata with placeholders.
        #
        self.filename = None
        self.mimetype = None
        self.extension = None

        #
        # Log the successful creation of the class.
        #
        self.prlog.log('debug', 'Created new PRDownloader instance.') 


    def get_record(self):
        #
        # Create the full download URL by appending the document_id to the
        # base URL of the MA Secretary of State Appeals website.
        #
        download_url = self.base_url + self.document_id

        #
        # Set a temporary filename for downloading the documents. This is so
        # the file can be analyzed before saving it permenantly.
        #
        self.tmpfile = os.path.join(self.temp_directory, self.document_id)

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
        self.prlog.log('info', 'Writing to ' + tmpfile)

        try:
            f = open(tmpfile, 'wb')
            try:
                shutil.copyfileobj(response, f)
            except IOError as e:
                self.prlog.log('debug', e)
                sys.exit('Could not save to temp file ' + self.tmpfile)
            finally:
                f.close()
        except OSError as e:
            self.prlog.log('debug', e)
            sys.exit('Could not open the temp file ' + self.tmpfile)

        #
        # Analyze the file to determine it's mimetype, which then in turn
        # can be used to give the file a proper extension. This also handles
        # non-existing files.
        #
        self.mimetype = self.get_metadata()

        #
        # If the mimetype and/or extension could not ultimately be determined,
        # this is the end for this particular document.
        #
        if self.mimetype is None or self.extension is None:
            return False

        #
        # With the extension determined, set the full path to the new
        # permenant file name.
        #
        fn = self.document_id + '.' + self.extension
        self.filename = os.path.join(self.download_path, fn)

        #
        # Move the temp file to the proper download location.
        #
        self.prlog.log('info', 'Moving temp file to ' + self.filename)
        try:
            shutil.move(self.tmpfile, self.filename)
        except IOError as e:
            self.prlog.log('debug', e)
            sys.exit('Could not move temp file to ' + self.filename)

        #
        # The document was downloaded and saved successfully.
        #
        return True

    def get_metadata(self):
        #
        # Determine the type of file downloaded. Usually it's either a Word
        # document, or a PDF.
        #
        mimetype = magic.from_file(self.tmpfile, mime=True)
        self.prlog.log('debug', 'Mimetype is ' + str(mimetype))

        #
        # The old binary MS Word documents (.doc) are difficult to read and
        # parse, so they need to be converted to the newer XML format (.docx)
        # which is handled by the command line version of LibreOffice. This has
        # the added benefit of retaining all the original metadata.
        #
        if mimetype == 'application/msword':
            self.tmpfile = self.convert_doc_to_docx(self.tmpfile,
                                                    self.document_id)

            #
            # If the file conversion failed for any reason, return the null
            # result. The metadata cannot be trusted if LibreOffice was unable
            # to read the file at all.
            #
            if self.tmpfile is None:
                return None

            #
            # Otherwise if successful, now re-check the metadata of the 
            # newly converted docx file.
            #
            return self.get_metadata()
        #
        # The mimetype was found and is supported.
        #
        elif mimetype in self.mimetypes:
            #
            # Match the discovered mimetype with allowable mimetypes to
            # determine the file extension.
            #
            self.extension = self.mimetypes[mimetype]
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
            return (None, None)

    def convert_doc_to_docx(self, tmpfile, document_id):
        #
        # The document conversion will be completed by LibreOffice, which
        # is invoked as `soffice` from the command line. Python can execute
        # external commands, but they must be built in list format. This also
        # sets the output directory to the temporary system directory that's
        # being used for all downloaded documents.
        #
        cmd = (['soffice', '--headless', '--convert-to', 'docx', '--outdir',
               self.temp_directory, tmpfile])

        #
        # All standard and error output which normally goes to the command
        # line is suppressed because it only matters if the command succeeds
        # or fails in this instance.
        #
        try:
            subprocess.run(cmd,
                           stdout=open(os.devnull, 'wb'),
                           stderr=open(os.devnull, 'wb'))
        except subprocess.CalledProcessError as e:
            self.prlog.log('debug', e)
            self.prlog.log('warning', 'Converting doc failed')
            return None

        #
        # When converted, LibreOffice uses the basename of the file (everything
        # before the extension -- which in this case there is no extension on
        # the temp file) and adds the '.docx' suffix. Normally this is printed
        # to the command line but it's easier to reconstruct the full path
        # rather than parse the output. For example:
        #
        # > soffice --headless --convert-to docx --outdir /tmp /tmp/tmpfile
        # convert /tmp/tempfile -> /tmp/tempfile.docx using filter ...
        #
        output_file = os.path.join(self.temp_directory, document_id + '.docx')

        #
        # But do test to make sure the file exists...
        #
        if not os.path.isfile(output_file):
            self.prlog.log('error', 'Converted file not found ' + output_file)
            return None

        return output_file


if __name__ == '__main__':
    pass
