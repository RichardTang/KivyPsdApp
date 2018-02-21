# coding:utf-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from struct import unpack, calcsize
from PIL import Image

from kivy.logger import Logger
import os

from util_indent_output import INDENT_OUTPUT
from util_file_parser import FileParser

from psd_modes import MODES
from util_psd_common_parser import PsdCommonParser

class PsdHeaderParser(PsdCommonParser):
  header = None
  
  def parse_header(self):
    Logger.info("")
    Logger.info("# Header #")

    self.header = {}

    C_PSD_HEADER = ">4sH 6B HLLHH"
    (
      self.header['sig'],
      self.header['version'],
      self.header['r0'],
      self.header['r1'],
      self.header['r2'],
      self.header['r3'],
      self.header['r4'],
      self.header['r5'],
      self.header['channels'],
      self.header['rows'],
      self.header['cols'],
      self.header['depth'],
      self.header['mode']
    ) = self._readf(C_PSD_HEADER)

    self.size = [self.header['rows'], self.header['cols']]
    #Logger.info("1111111")

    if self.header['sig'] != "8BPS":
      raise ValueError("Not a PSD signature: '%s'" % self.header['sig'])
    if self.header['version'] != 1:
      raise ValueError("Can not handle PSD version:%d" % self.header['version'])
    self.header['modename'] = MODES[self.header['mode']] if 0 <= self.header['mode'] < 16 else "(%s)" % self.header['mode']
    #Logger.info("22222222")

    Logger.info(INDENT_OUTPUT(1, "channels:%(channels)d, rows:%(rows)d, cols:%(cols)d, depth:%(depth)d, mode:%(mode)d [%(modename)s]" % self.header))
    Logger.info(INDENT_OUTPUT(1, "%s" % self.header))

    # Remember position
    self.header['colormodepos'] = self.fd.tell()
    self._skip_block("color mode data", 1)


  