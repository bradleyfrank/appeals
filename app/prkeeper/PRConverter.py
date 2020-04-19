#!/usr/bin/env python

__author__ = 'Bradley Frank'

import os
import re
import subprocess
import sys


class PRConverter:

    def __init__(self, prlog):
        #
        # The current logger for the application.
        #
        self.prlog = prlog

        #
        # Log the successful creation of the class.
        #
        self.prlog.log('debug', 'Created new PRConverter instance.')

    def convert_doc_to_docx(self, output_dir, file_to_convert):
        #
        # The document conversion will be completed by LibreOffice, which
        # is invoked as `soffice` from the command line. Python can execute
        # external commands, but they must be built in list format. This also
        # sets the output directory to that of the raw downloads.
        #
        cmd = (['soffice', '--headless', '--convert-to', 'docx', '--outdir',
               output_dir, file_to_convert])
        self.prlog.log('debug', 'Running ' + cmd)

        #
        # Capture the output of the command in order to ensure the document
        # is converted and the file exists. For example:
        #
        # > soffice --headless --convert-to docx --outdir /tmp /tmp/doc
        # convert /tmp/doc -> /tmp/doc.docx using filter : Office Open XML Text
        #
        try:
            out = subprocess.check_output(cmd)
        except subprocess.CalledProcessError as e:
            self.prlog.log('debug', e)
            self.prlog.log('warning', 'Converting doc failed')
            return None

        #
        # The subprocess output is saved as bytes, so convert it to a string.
        # Then, split that string at the "->" character, which is a convenient
        # way to discard the input file name. This should result in a list with
        # two elements, for example:
        #
        # [
        #   'convert /tmp/doc ',
        #   ' /tmp/doc.docx using filter : Office Open XML Text\n'
        # ]    
        #
        result = out.decode('utf-8').split('->')
        self.prlog.log('debug', 'Libreoffice output is ' + result)

        #
        # Use a regular expression search to find the full file name and path
        # of the converted document. This searches only the second element of
        # the list returned above.
        #
        # For example, the regex will match '/tmp/doc.docx' from the string
        # ' /tmp/doc.docx using filter : Office Open XML Text\n'.
        #
        match = re.search('\/[^\0]+\.docx', result[1])

        #
        # Test if a match was found in the output; if not, the conversion
        # failed, otherwise, the output file is found.
        #
        if match is None:
            return None
        else:
            output_file = match.group(0)
            self.prlog.log('info', 'Document was converted to ' + output_file)

        #
        # For good measure, test to make sure the converted file exists.
        #
        if not os.path.isfile(output_file):
            self.prlog.log('error', 'Converted file not found ' + output_file)
            return None

        return output_file