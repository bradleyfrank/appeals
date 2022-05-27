#!/usr/bin/env python3

__author__ = 'Bradley Frank'

import os
import sys
from typing import Dict

import utils
from prkeeper import PRAnalyzer
from prkeeper import PRDownloader
from prkeeper import PRConverter

import logzero

CONFIGS = None
LOGGING_LEVELS = {
    "normal": {"output": logzero.INFO, "format": "%(color)s%(message)s%(end_color)s"},
    "verbose": {"output": logzero.DEBUG, "format": "%(color)s%(message)s%(end_color)s"},
    "debug": {
        "output": logzero.DEBUG,
        "format": (
            "[%(levelname)8s %(asctime)s %(funcName)s:%(lineno)d] "
            "%(color)s%(message)s%(end_color)s"
        ),
    },
}


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
        logger.warning("Document is unexpected/unsupported mimetype")
        return (None, None)


def get_documents(prlog, start_date):
    """Download and process documents."""

    logger.info(f"Beginning downloads from date {start_date}")

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


USER_FLAGS = utils.argparser()
CONFIGS = utils.get_configs(USER_FLAGS.config)
utils.configure_logging(USER_FLAGS.verbose)

#
# Download the documents. The first method:
# A specific start date is set.
#
if USER_FLAGS.date:
    pass
#
# Download the documents. The second method:
# Resume from the last document present.
#
else:
    pass
