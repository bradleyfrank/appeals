#!/usr/bin/env python

__author__ = 'Bradley Frank'

import os
import sys
import yaml


class PRConfReader:

    def __init__(self, prlog):
        self.prlog = prlog

    def get_configs(self):
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
        conf = os.path.join(__location__, 'prkeeper.yaml')
        try:
            f = open(conf, 'r')
            try:
                cfg = yaml.safe_load(f)
            except yaml.YAMLError as e:
                self.prlog.log('debug', e)
                sys.exit('Could not load yaml file ' + conf)
            finally:
                f.close()
        except OSError as e:
            self.prlog.log('debug', e)
            sys.exit('Could not open config file ' + conf)

        return cfg

if __name__ == '__main__':
    pass