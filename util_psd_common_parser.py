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

class PsdCommonParser(FileParser):
  
  def _pad2(self, i):
    """same or next even"""
    return (i + 1) / 2 * 2

  def _pad4(self, i):
    """same or next multiple of 4"""
    return (i + 3) / 4 * 4

