#!/usr/bin/env python

__author__ = 'Bradley Frank'

#
# Import standard Python libraries.
#
import datetime
import os
import sys
import tempfile

#
# Import custom independent functions.
#   import <filename> as <function reference>
#
# Then call imported functions like so: <function reference>.<function name>
#
import helpers as helpers

#
# Import custom classes.
#   from <directory> import <filename>
#
# Then call imported classes like so: <filename>.<class name>
#
from prkeeper import PRAnalyzer
from prkeeper import PRConverter
from prkeeper import PRDownloader
from prkeeper import PRLogger

CONFIGS = None

def get_documents(prlog, start_range, end_range):
    """Download and process documents."""
    #
    # Log the download range.
    #
    prlog.log('info', 'Beginning new run with range ' +
              str(start_range) + ' to ' + str(end_range))

    #
    # Variable that ultimately allows or stops document downloading.
    #
    continue_downloads = True

    #
    # Today's date for comparison to document creation date.
    #
    today = datetime.datetime.now()

    #
    # The document ID that is being downloaded. Set to the start_range
    # to begin; gets incremented within the download loop after that.
    #
    document_id = start_range

    #
    # Create an instance of PRDownloader which will handle downloading and
    # saving the documents.
    #
    prdl = PRDownloader.PRDownloader(
        prlog,
        CONFIGS['prdownloader']['base_url'],
        CONFIGS['prdownloader']['download_path_raw'],
        CONFIGS['prdownloader']['download_path_final']
    )

    #
    # Create an instance of PRAnalyzer which collects metadata and performs
    # text extraction from documents.
    #
    przy = PRAnalyzer.PRAnalyzer(prlog)

    #
    # Loop through the given document range, downloading incrementally.
    #
    while continue_downloads is True:
        #
        # Calls the function to handle the download, passing the document ID
        # to download.
        #
        rawfile = prdl.download_document(document_id)

        #
        # Should downloading fail, the intention is to skip to the next
        # document and not exit the program.
        #
        if rawfile is None:
            continue

        #
        # Ensure the raw download is a valid type of file.
        #
        document, mimetype = filter_document(prlog, przy, rawfile)

        #
        # If the mimetype and/or extension could not ultimately be determined,
        # this is the end for this particular document.
        #
        if document is None or mimetype is None:
            continue

        #
        #
        #
        extension = przy.get_extension(document,
                                       mimetype,
                                       CONFIGS['general']['valid_mimetypes'])

        #
        #
        #
        filename = document_id + extension

        #
        #
        #
        prdl.save_document(document, filename)

        #
        # The creation date of the document is used to inform the program
        # to continue or stop downloading further documents (since in
        # theory there wouldn't be documents with creation dates in the
        # future), even if the program hasn't reached the end of a
        # specified range given by the user. The first step is to extract
        # the creation date.
        #
        creation_date = przy.get_creation_date(document)
    else:
        prlog.log('warning', 'Downloading ' + str(document_id) + ' failed')

def filter_document(prlog, przy, document):
    """Ensure document is type Word or PDF."""
    #
    # Analyze the file to determine it's mimetype, which then in turn
    # can be used to give the file a proper extension.
    #
    mimetype = przy.find_mimetype(document)

    #
    # The old binary MS Word documents (.doc) are difficult to read and
    # parse, so they need to be converted to the newer XML format (.docx)
    # which is handled by the command line version of LibreOffice. This has
    # the added benefit of retaining all the original metadata.
    #
    if mimetype == 'application/msword':
        prvt = PRConverter.PRConverter(prlog)
        document = prvt.convert_doc_to_docx(
            CONFIGS['prdownloader']['download_path_raw'],
            document
        )

        #
        # If the file conversion failed for any reason, stop processing
        # the file. The metadata cannot be trusted if LibreOffice was
        # unable to read the file.
        #
        if document is None:
            return (None, None)

        #
        # Otherwise re-check the mimetype of the newly converted docx file.
        #
        return filter_document(prlog, przy, document)
    #
    # The mimetype was found and is supported, return file metadata.
    #
    elif mimetype in CONFIGS['general']['valid_mimetypes']:
        return document, mimetype
    #
    # If the mimetype is unsupported, or couldn't be determined, end here,
    # setting the document's attributes to null. It's a good indication
    # there existed no file with this ID and the website returned an html
    # document, which represents the site redirecting back to the main
    # search page.
    #
    else:
        self.prlog.log('warning', 'Document is unexpected/unsupported
                        mimetype')
        return (None, None)

#
# Build a set of options that is available to the user.
#
arguments = helpers.create_arguments()

#
# Read the settings passed to the script by the user. The parse_args() function
# comes from the "argparse" Python module.
#
user_settings = arguments.parse_args()

#
# Sets logging for the application: adds additional conole output if
# the debug argument is passed, otherwise just logs to file by default.
#
if user_settings.debug:
    prlog = PRLogger.PRLogger(LOG_FILE, log_to_console=True)
else:
    prlog = PRLogger.PRLogger(LOG_FILE)

#
# Read configuration file.
#
CONFIGS = helpers.get_configs(prlog)

#
# If s3 was selected, setup the bucket if one does not exist already.
# Otherwise, ensure the download directory exists on disk.
#
if user_settings.s3:
    pass
elif not os.path.isdir(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)

#
# Download the documents. The first method:
# A range of documents to download, i.e. the "scope" argument is set.
#
if user_settings.scope:
    #
    # The high-end value can only be less than the low-end value if the
    # high-end value is 0, which means begin at the low-end value and
    # continue until reaching the end.
    #
    if user_settings.scope[1] == 0:
        get_documents(prlog, user_settings.scope[0], None)
    #
    # If the high-end value is less than the low-end value, exit with error.
    #
    elif user_settings.scope[1] < user_settings.scope[0]:
        sys.exit('Start range cannot be greater than end range.')
    #
    # Otherwise a nominal range was given, proceed to download those documents.
    #
    else:
        get_documents(prlog, user_settings.scope[0], user_settings.scope[1])
#
# Download the documents. The second method:
# Start from where last left off, i.e. the "resume" argument is set.
#
elif user_settings.resume:
    prlog.log('info', 'Resuming downloads')
    # TODO: get last downloaded document
    # get_documents(start_value, None)
#
# This catches a scenario where somehow neither --resume nor --scope was set.
# Lack of those arguments should be caught by argparser, so this if this is
# executed, there's an error present somewhere else.
#
else:
    pass

prlog.log('debug', 'Ending current run\n')
