#!/usr/bin/env python

__author__ = 'Bradley Frank'

import argparse
import os
import sys
import tempfile
from prkeeper import PRAnalyzer
from prkeeper import PRConfReader
from prkeeper import PRDownloader
from prkeeper import PRLogger

#
# General script variables:
#
# DOWNLOAD_PATH: local save location for downloaded documents
# LOG_FILE: application-wide log file
#
DOWNLOAD_PATH = '/opt/prkeeper/downloads/appeals'
LOG_FILE = '/opt/prkeeper/logs/prkeeper.log'


def create_arguments():
    #
    # Set available command-line arguments.
    #
    arguments = argparse.ArgumentParser(
        description='Downloads Massachusetts public records.')

    #
    # --debug
    # Prints all debug messages to the console.
    #
    arguments.add_argument('-d', '--debug', action='store_true',
                           help='enables console debug messages')

    #
    # --resume | --scope
    # Downloads can be expressed in an explicit range, or resumed from a prior
    # run of the program. Continuing is the default setting. The last download
    # is tracked in the status file. These settings are mutually exclusive.
    #
    download_method = arguments.add_mutually_exclusive_group(required=True)
    download_method.add_argument('-r', '--resume', action='store_true',
                                 help='resumes downloading from a prior run')
    download_method.add_argument('-s', '--scope', type=int, nargs=2,
                                 help='download documents between start and \
                                 end values (inclusive); set end value to 0 \
                                 to download all available documents after \
                                 start value')

    #
    # --s3
    # Saves documents to an AWS s3 bucket. By default the documents save to
    # disk, but s3 can also be used. Credentials for AWS should be entered
    # into the credentials.env file found in this Git repo.
    #
    arguments.add_argument('--s3', action='store_true',
                           help='saves downloads to aws s3 bucket')

    return arguments


def get_documents(start_range, end_range):
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
    # Latest document successfully downloaded.
    #
    latest_document = None

    #
    # The document ID that is being downloaded. Set to the start_range
    # to begin; gets incremented within the download loop after that.
    #
    document_id = start_range

    #
    # Instantiant the downloader class, providing a temporary directory
    # to use as scratch space to save downloads.
    #
    prdl = PRDownloader.PRDownloader(prlog, prcfg, DOWNLOAD_PATH,
                                     tempfile.mkdtemp())

    #
    # Loop through the given document range, downloading incrementally.
    #
    while continue_downloads is True:
        #
        # Calls the function to handle the download, passing the document ID
        # to download. PRDownloader tracks document attributes as it downloads
        # each file. It will return False if the download fails at any point.
        # Should it fail, the intention is to skip to the next document and
        # not exit the program.
        #
        if prdl.get_record(document_id) is not False:
            #
            # Collect document attributes to use for analzying.
            #
            filename = prdl.get_filename(document_id)
            mimetype = prdl.get_mimetype(document_id)
            extension = prdl.get_extension(document_id)

            #
            # Creates an PRAnalyzer instance for gathering metadata and parsing
            # text of the document for uploading to the database.
            #
            DOCUMENTS[document_id] = PRAnalyzer.PRAnalyzer(prlog,
                                                           filename,
                                                           mimetype,
                                                           extension)

            #
            # The creation date of the document is used to inform the program
            # to continue or stop downloading further documents (since in
            # theory there wouldn't be documents with creation dates in the
            # future), even if the program hasn't reached the end of a
            # specified range given by the user. The first step is to extract
            # the creation date.
            #
            # creation_date = DOCUMENTS[document_id].get_creation_date()
        else:
            prlog.log('warning', 'Downloading ' + str(document_id) + ' failed')


#
# Setup and read arguments given to the script.
#
args = create_arguments().parse_args()

#
# Sets logging for the application: adds additional conole output if
# the debug argument is passed, otherwise just logs to file by default.
#
if args.debug:
    prlog = PRLogger.PRLogger(LOG_FILE, log_to_console=True)
else:
    prlog = PRLogger.PRLogger(LOG_FILE)

#
# Read configuration file.
#
prcr = PRConfReader.PRConfReader(prlog)
prcfg = prcr.get_configs()

#
# If s3 was selected, setup the bucket if one does not exist already.
# Otherwise, ensure the download directory exists on disk.
#
if args.s3:
    pass
elif not os.path.isdir(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)

#
# Download the documents. The first method:
# A range of documents to download, i.e. the "scope" argument is set.
#
if args.scope:
    #
    # The high-end value can only be less than the low-end value if the
    # high-end value is 0, which means begin at the low-end value and
    # continue until reaching the end.
    #
    if args.scope[1] == 0:
        get_documents(args.scope[0], None)
    #
    # If tThe high-end value is less than the low-end value, exit with error.
    #
    elif args.scope[1] < args.scope[0]:
        sys.exit('Start range cannot be greater than end range.')
    #
    # Otherwise a nominal range was given.
    #
    else:
        #
        # A regular scope was provided, proceed to download those documents.
        #
        get_documents(args.scope[0], args.scope[1])
#
# Download the documents. The second method:
# Start from where last left off, i.e. the "resume" argument is set.
#
elif args.resume:
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
