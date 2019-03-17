#!/usr/bin/env python3

__author__ = 'Bradley Frank'

import argparse
import logging
import os
import shutil
import subprocess
import sys
import urllib.request

base_url = 'https://www.sec.state.ma.us/AppealsWeb/Download.aspx?DownloadPath='
download_path = '/home/bfrank/Downloads/Public_Records'

def get_record(fileID):

    download_url = base_url + fileID
    #print('Downloading file ' + fileID + '.')

    try:
        document = urllib.request.urlopen(download_url)
    except HTTPError as e:
        print('Could not download file ID ' + fileID + '.')
        return False
    except URLError as e:
        print('Could not download file ID ' + fileID + '.')
        return False

    filename = os.path.join(download_path, fileID + '.pdf')

    # Create repo directory if it doesn't exist
    if not os.path.isdir(download_path):
        os.makedirs(download_path, exist_ok=True)

    # Skip if file already exists
    if os.path.isfile(filename):
        print('File already downloaded.')
        return False

    # Save the document to disk
    try:
        with open(filename, 'wb') as f:
            shutil.copyfileobj(document, f)
    except IOError as e:
        print(e)
        return False

    return True

for d in range(10950, 11000):
    fileID = str(d)
    get_record(fileID)
