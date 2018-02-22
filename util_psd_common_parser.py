# coding:utf-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from struct import unpack, calcsize
from PIL import Image

from kivy.logger import Logger
import os

from util_indent_output import INDENT_OUTPUT
from psd_resource_descriptions import RESOURCE_DESCRIPTIONS

from util_file_parser import FileParser

from psd_modes import MODES

class PsdCommonParser(FileParser):
  
  def _pad2(self, i):
    """same or next even"""
    return (i + 1) / 2 * 2

  def _pad4(self, i):
    """same or next multiple of 4"""
    return (i + 3) / 4 * 4
  
  def parse_irb(self):
    """return total bytes in block"""
    r = {}
    r['at'] = self.fd.tell()
    (r['type'], r['id'], r['namelen']) = self._readf(">4s H B")
    n = self._pad2(r['namelen'] + 1) - 1
    (r['name'],) = self._readf(">%ds" % n)
    r['name'] = r['name'][:-1] # skim off trailing 0byte
    r['short'] = r['name'][:20]
    (r['size'],) = self._readf(">L")
    self.fd.seek(self._pad2(r['size']), 1) # 1: relative
    r['rdesc'] = "[%s]" % RESOURCE_DESCRIPTIONS.get(r['id'], "?")
    Logger.info(INDENT_OUTPUT(1, "Resource: %s" % r))
    Logger.info(INDENT_OUTPUT(1, "0x%(at)06x| type:%(type)s, id:%(id)5d, size:0x%(size)04x %(rdesc)s '%(short)s'" % r))
    self.ressources.append(r)
    return 4 + 2 + self._pad2(1 + r['namelen']) + 4 + self._pad2(r['size'])
            
