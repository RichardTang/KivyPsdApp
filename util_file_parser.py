# coding:utf-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from struct import unpack, calcsize
from PIL import Image

from kivy.logger import Logger
import os

from util_indent_output import INDENT_OUTPUT


class FileParser(object):

    def _readf(self, format):
        """read a strct from file structure according to format"""
        return unpack(format, self.fd.read(calcsize(format)))

    def _skip_block(self, desc, indent=0, new_line=False):
        (n,) = self._readf('>L') # (n,) is a 1-tuple.
        if n:
            self.fd.seek(n, 1) # 1: relative

        if new_line:
            Logger.info('')
        Logger.info(INDENT_OUTPUT(indent, 'Skipped %s with %s bytes' % (desc, n)))


