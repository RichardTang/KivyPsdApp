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
from util_psd_header_parser import PsdHeaderParser

class PsdImageResourceParser(PsdHeaderParser):
  pass
  