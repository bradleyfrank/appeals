#!/usr/bin/env python

__author__ = 'Bradley Frank'

import argparse
import yaml

def create_arguments():
    """Create script arguments."""
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
    """Read in settings from config file."""
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