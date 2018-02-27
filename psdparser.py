# coding:utf-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from struct import unpack, calcsize
from PIL import Image

from kivy.logger import Logger
import os

from psd_channel_suffixes import CHANNEL_SUFFIXES
from psd_resource_descriptions import RESOURCE_DESCRIPTIONS
from psd_modes import MODES
from psd_compressions import  COMPRESSIONS
from psd_blendings import BLENDINGS
from psd_pil_bands import PIL_BANDS

from util_indent_output import INDENT_OUTPUT
from util_psd_layer_parser import PsdLayerParser

class PSDParser(PsdLayerParser):
  num_layers = 0
  layers = None

  def __init__(self, filename):
    self.filename = filename

  def parse(self):
    Logger.info("Opening '%s'" % self.filename)
    self.fd = open(self.filename, 'rb')
    try:
      self.parse_header()
      self.parse_image_resources()
      self.parse_layers_and_masks()
      #self.parse_image_data()
    finally:
      self.fd.close()
    Logger.info("")
    Logger.info("DONE")

  def parse_image_data(self):
    if not self.header:
      self.parse_header()
    if not self.ressources:
      self._skip_block("image resources", new_line=True)
      self.ressources = 'not parsed'
    if not self.layers:
      self._skip_block("image layers", new_line=True)
      self.layers = 'not parsed'
    self.merged_image = []
    li = {}
    li['chids'] = range(self.header['channels'])
    li['chlengths'] = [ None ] * self.header['channels'] # dummy data
    (li['name'], li['channels'], li['rows'], li['cols']) = ('merged', self.header['channels'], self.header['rows'], self.header['cols'])
    li['layernum'] = -1
    self.parse_image(li, is_layer=False)
    if li['channels'] == 1:
      self.merged_image = self.merged_image[0]
    elif li['channels'] == 3:
      self.merged_image = Image.merge('RGB', self.merged_image)
    elif li['channels'] >= 4 and self.header['mode'] == 3:
      self.merged_image = Image.merge('RGBA', self.merged_image[:4])
    else:
      raise ValueError('Unsupported mode or number of channels')

