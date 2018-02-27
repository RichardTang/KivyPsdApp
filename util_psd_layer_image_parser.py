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
from util_psd_layer_descriptor_parser import PsdLayerDescriptorParser
from psd_compressions import  COMPRESSIONS
from psd_pil_bands import PIL_BANDS
from psd_channel_suffixes import CHANNEL_SUFFIXES

class PsdLayerImageParser(PsdLayerDescriptorParser):
  images = None
  merged_image = None

  def parse_channel(self, li, idx, count, rows, cols, depth, is_layer=True):
    """params:
    li -- layer info struct
    idx -- channel number
    count -- number of channels to process ???
    rows, cols -- dimensions
    depth -- bits
    """
    chlen = li['chlengths'][idx]
    if chlen is not None  and  chlen < 2:
      raise ValueError("Not enough channel data: %s" % chlen)
    if li['chids'][idx] == -2:
      rows, cols = li['mask']['rows'], li['mask']['cols']

    rb = (cols * depth + 7) / 8 # round to next byte

    # channel header
    chpos = self.fd.tell()
    (comp,) = self._readf(">H")

    if chlen:
      chlen -= 2

    pos = self.fd.tell()

    # If empty layer
    if cols * rows == 0:
      Logger.info(INDENT_OUTPUT(1, "Empty channel, skiping"))
      return

    if COMPRESSIONS.get(comp) == 'RLE':
      #Logger.info(INDENT_OUTPUT(1, "Handling RLE compressed data"))
      rlecounts = 2 * count * rows
      if chlen and chlen < rlecounts:
        raise ValueError("Channel too short for RLE row counts (need %d bytes, have %d bytes)" % (rlecounts,chlen))
      pos += rlecounts # image data starts after RLE counts
      rlecounts_data = self._readf(">%dH" % (count * rows))
      for ch in range(count):
        #Logger.info('ch=%d' % ch)
        rlelen_for_channel = sum(rlecounts_data[ch * rows:(ch + 1) * rows])
        #Logger.info('000001')
        data = self.fd.read(rlelen_for_channel)
        #Logger.info('0000011')
        #Logger.info('idx=%d' % idx)
        #Logger.info('%d' % (li['chids'][idx]))
        channel_name = CHANNEL_SUFFIXES[li['chids'][idx]]
        #Logger.info('000002')
        if li['channels'] == 2 and channel_name == 'B': channel_name = 'L'
        p = Image.fromstring("L", (cols, rows), data, "packbits", "L" )
        #Logger.info('000003')
        if is_layer:
          #Logger.info('0000030')
          if channel_name in PIL_BANDS:
            #Logger.info('0000031')
            self.images[li['idx']][PIL_BANDS[channel_name]] = p
        else:
          #Logger.info('0000032')
          self.merged_image.append(p)
        #Logger.info('000004')
    elif COMPRESSIONS.get(comp) == 'Raw':
      #Logger.info(INDENT_OUTPUT(1, "Handling Raw compressed data"))

      for ch in range(count):
        data = self.fd.read(cols * rows)
        channel_name = CHANNEL_SUFFIXES[li['chids'][idx]]
        if li['channels'] == 2 and channel_name == 'B': channel_name = 'L'
        p = Image.fromstring("L", (cols, rows), data, "raw", "L")
        if is_layer:
          if channel_name in PIL_BANDS:
            self.images[li['idx']][PIL_BANDS[channel_name]] = p
        else:
          self.merged_image.append(p)

    else:
      # TODO: maybe just skip channel...:
      #   f.seek(chlen, SEEK_CUR)
      #   return
      raise ValueError("Unsupported compression type: %s" % COMPRESSIONS.get(comp, comp))
    #Logger.info('000005')
    #Logger.info('chlen=%d' % chlen)
    #Logger.info('chpos=%d' % chpos)
    if (chlen is not None) and (self.fd.tell() != chpos + 2 + chlen):
      Logger.info("currentpos:%d should be:%d!" % (self.fd.tell(), chpos + 2 + chlen))
      self.fd.seek(chpos + 2 + chlen, 0) # 0: SEEK_SET
    #Logger.info('end of parse channel')
    return


  def parse_image(self, li, is_layer=True):
    if not self.header:
      self.parse_header()
    if not self.ressources:
      self._skip_block("image resources", new_line=True)
      self.ressources = 'not parsed'

    #Logger.info("")
    #Logger.info("# Image: %s/%d #" % (li['name'], li['channels']))

    # channels
    if is_layer:
      for ch in range(li['channels']):
        self.parse_channel(li, ch, 1, li['rows'], li['cols'], self.header['depth'], is_layer)
    else:
      self.parse_channel(li, 0, li['channels'], li['rows'], li['cols'], self.header['depth'], is_layer)
    #Logger.info('end of parse image')
    return
