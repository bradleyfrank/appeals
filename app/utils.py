#!/usr/bin/env python

"""Various helper functions.
"""

import argparse
import json
from pathlib import PosixPath
from typing import Union, Dict
import logzero

DEFAULT_CONFIG_FILE = "/opt/app/conf.yml"
LOGGING_LEVELS = [
    {"output": logzero.INFO, "format": "%(color)s%(message)s%(end_color)s"},
    {"output": logzero.DEBUG, "format": "%(color)s%(message)s%(end_color)s"},
    {
        "output": logzero.DEBUG,
        "format": (
            "[%(levelname)8s %(asctime)s %(funcName)s:%(lineno)d] "
            "%(color)s%(message)s%(end_color)s"
        ),
    },
]

def argparser():
    """Create script arguments."""
    #
    # Set available command-line arguments.
    #
    arguments = argparse.ArgumentParser(description="Downloads Massachusetts public records.")

    #
    # --config
    # Specifies an alternate config file.
    #
    arguments.add_argument(
        "-c", "--config", help="path to directory with config file", default=DEFAULT_CONFIG_FILE
    )

    #
    # --verbose
    # Prints additional information, or debug messages, to the console.
    # Supports up to two levels of verbosity.
    #
    arguments.add_argument('-v', '--verbose', action='count', default=0, help="prints additional information")

    #
    # --resume | --from
    # Downloads can begin from a specific date, or resumed from a prior
    # run of the program. Resuming is the default setting.
    #
    download_method = arguments.add_mutually_exclusive_group()
    download_method.add_argument(
        "-r", "--resume", action="store_true", help="resumes downloading from last document"
    )
    download_method.add_argument(
        "-d", "--date", help="download documents from a specific date"
    )

    return arguments.parse_args()


def configure_logging(verbosity: int = 0) -> None:
    """Configures logzero verbosity."""

    logzero.loglevel(LOGGING_LEVELS[verbosity]["output"])
    logzero.formatter(formatter=logzero.LogFormatter(fmt=LOGGING_LEVELS[verbosity]["format"]))


def get_configs(config_file: Union[str, PosixPath]) -> Dict:
    """Read in settings from the config file."""

    if isinstance(config_file, str):
        config_file = PosixPath(config_file)

    if not config_file.is_file():
        raise FileNotFoundError(f"No config file at {config_file}")

    with open(config_file, encoding="utf-8", mode="rt") as json_file:
        return json.load(json_file)
