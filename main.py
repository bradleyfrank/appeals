#!/usr/bin/env python

__author__ = 'Bradley Frank'

import argparse
import os
import sys
import tempfile
import yaml
from prkeeper import PRAnalyzer
from prkeeper import PRConfReader
from prkeeper import PRDownloader
from prkeeper import PRLogger

CONFIGS = None


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


def get_configs(prlog):
    #
    # Get the current working directory of this script.
    #
    # The join() call prepends the current working directory, but the
    # documentation says that if some path is absolute, all other paths
    # left of it are dropped. Therefore, getcwd() is dropped when
    # dirname(__file__) returns an absolute path. The realpath call
    # resolves symbolic links if any are found.
    #
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))

    #
    # Open and load the configuration file.
    #
    conf = os.path.join(__location__, 'configs.yaml')
    try:
        f = open(conf, 'r')
        try:
            configs = yaml.safe_load(f)
        except yaml.YAMLError as e:
            prlog.log('debug', e)
            sys.exit('Could not load yaml file ' + conf)
        finally:
            f.close()
    except OSError as e:
        prlog.log('debug', e)
        sys.exit('Could not open config file ' + conf)

    return configs


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
    # Instantiant the downloader class which will handle downloading and
    # saving the documents.
    #
    prdl = PRDownloader.PRDownloader(prlog, CONFIGS)

    #
    # Loop through the given document range, downloading incrementally.
    #
    while continue_downloads is True:
        #
        # Calls the function to handle the download, passing the document ID
        # to download. It will return False if the download fails at any point.
        #
        raw_document = prdl.download_document(document_id)

        #
        # Should it fail, the intention is to skip to the next document and
        # not exit the program.
        #
        if raw_document is False:
            continue

        #
        # Creates an PRAnalyzer instance for gathering metadata and parsing
        # text of the document for uploading to the database.
        #
        DOCUMENTS[document_id] = PRAnalyzer.PRAnalyzer(prlog, raw_document)

        #
        # Analyze the file to determine it's mimetype, which then in turn
        # can be used to give the file a proper extension. This also handles
        # non-existing files.
        #
        mimetype = DOCUMENTS[document_id].find_mimetype()

        #
        # If the mimetype and/or extension could not ultimately be determined,
        # this is the end for this particular document.
        #
        if self.mimetype is None or self.extension is None:
            return False

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
CONFIGS = get_configs(prlog)

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
