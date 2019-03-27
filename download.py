#!/usr/bin/env python

__author__ = 'Bradley Frank'

import argparse
import logging
import magic
import mimetypes
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request

base_url = 'https://www.sec.state.ma.us/AppealsWeb/Download.aspx?DownloadPath='
download_path = '/Users/bfrank/Downloads/Public_Records'

def get_record(file_ID, temp_directory):

    download_url = base_url + file_ID

    try:
        response = urllib.request.urlopen(download_url)
    except HTTPError as e:
        print('Could not download file ID ' + file_ID + '.')
        return False
    except URLError as e:
        print('Could not download file ID ' + file_ID + '.')
        return False

    tmpfile = os.path.join(temp_directory, file_ID)

    try:
        with open(tmpfile, 'wb') as f:
            shutil.copyfileobj(response, f)
    except IOError as e:
        print(e)
        return False

    mime = magic.from_file(tmpfile, mime=True)

    if mime is None:
        return False
    elif mime == 'application/msword':
        ext = '.doc'
    elif mime == 'application/pdf':
        ext = '.pdf'
    else:
        ext = mimetypes.guess_extension(mime, True)

    filename = os.path.join(download_path, file_ID + ext)

    # Create download directory if it doesn't exist
    if not os.path.isdir(download_path):
        os.makedirs(download_path, exist_ok=True)

    # Move the temp file into place
    os.rename(tmpfile, filename)

    return True

temp_directory = tempfile.mkdtemp()
for d in range(1, 5):
    file_ID = str(d)
    get_record(file_ID.zfill(5), temp_directory)
