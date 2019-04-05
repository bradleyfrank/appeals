#!/usr/bin/env python3.4

__author__ = 'Bradley Frank'

import argparse
from prkeeper.logger import PRLogger
from prkeeper.download import PRDownloader

#
# General script variables:
#
# DOWNLOAD_PATH: save location for all downloaded documents
# LOG_FILE: application-wide log file
#
DOWNLOAD_PATH = '/srv/public_records/downloads/appeals'
LOG_FILE = '/srv/public_records/logs/prkeeper.log'


def set_arguments():
    #
    # Set available command-line arguments.
    #
    arguments = argparse.ArgumentParser(
        description='Downloads Massachusetts public record appeals.')

    #
    # --debug
    # Prints all debug messages to the console.
    #
    arguments.add_argument('-d', '--debug', action='store_true',
                           help='enables debug messages')

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


arguments = set_arguments()
args = arguments.parse_args()

#
# Sets logging for the application: adds additional conole output if
# the debug argument is passed, otherwise just logs to file by default.
#
if args.debug:
    prlog = PRLogger(LOG_FILE, log_to_console=True)
else:
    prlog = PRLogger(LOG_FILE)

#
# One of two download methods must be given to begin downloading: (a) a
# range of documents to download, or (b) resume downloading from where
# last left off.
#
if args.scope:
    if args.scope[1] < args.scope[0] and args.scope[1] != 0:
        sys.exit('Start range cannot be greater than end range.')
    else:
        # Copy the arguments to a new stand-alone variable.
        download_range = args.scope.copy()
        # Make the ending range inclusive, as the user would expect.
        download_range[1] = download_range[1] + 1
        # Log the download method.
        prlog.log('info', 'Beginning new run with range ' +
                  str(download_range[0]) + ' to ' + str(download_range[1]))
else:
    prlog.log('info', 'Resuming downloads')

#
# If s3 was selected, setup the bucket if one does not exist already.
# Otherwise, ensure the download directory exists on disk.
#
if args.s3:
    pass
elif not os.path.isdir(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)

#
# Instantiate the prkeeper class with provided settings.
#
prkeeper = PublicRecordKeeper(prlog, DOWNLOAD_PATH)

#
# Loop through the specified range to download documents.
#
for document in range(download_range[0], download_range[1]):
    prkeeper.get_records(document)

prlog.log('debug', 'Ending current run\n')
