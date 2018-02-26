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
from util_psd_image_resource_parser import PsdImageResourceParser
from psd_channel_suffixes import CHANNEL_SUFFIXES
from psd_blendings import BLENDINGS
from util_psd_layer_image_parser import PsdLayerImageParser

class PsdLayerParser(PsdLayerImageParser):
  def parse_layer_blend_mode(self):
    #
    # Blend mode
    #
    bm = {}
    (bm['sig'], bm['key'], bm['opacity'], bm['clipping'], bm['flags'], bm['filler'],
    ) = self._readf(">4s4sBBBB")
    bm['opacp'] = (bm['opacity'] * 100 + 127) / 255
    bm['clipname'] = bm['clipping'] and "non-base" or "base"
    bm['blending'] = BLENDINGS.get(bm['key'])
    Logger.info(INDENT_OUTPUT(3, "Blending mode: sig=%(sig)s key=%(key)s opacity=%(opacity)d(%(opacp)d%%) clipping=%(clipping)d(%(clipname)s) flags=%(flags)x" % bm))
    return bm
  
  def parse_layer_mask(self):
    #
    # Layer mask data
    #
    m = {}
    (m['size'],) = self._readf(">L")
    if m['size']:
      (m['top'], m['left'], m['bottom'], m['right'], m['default_color'], m['flags'],
      ) = self._readf(">llllBB")
      # skip remainder
      self.fd.seek(m['size'] - 18, 1) # 1: SEEK_CUR
      m['rows'], m['cols'] = m['bottom'] - m['top'], m['right'] - m['left']
    return m

  def merge_image(self, linfo):
    for i in range(self.num_layers):
      # Empty layer
      if linfo[i]['rows'] * linfo[i]['cols'] == 0:
        self.images.append(None)
        self.parse_image(linfo[i], is_layer=True)
        continue
      self.images.append([0, 0, 0, 0])
      self.parse_image(linfo[i], is_layer=True)
      Logger.info('XXXXXX i=%d rows=%d cols=%d' % (i,linfo[i]['rows'],linfo[i]['cols']))
      if linfo[i]['channels'] == 2:
        l = self.images[i][0]
        a = self.images[i][3]
        self.images[i] = Image.merge('LA', [l, a])
      else:
        # is there an alpha channel?
        if type(self.images[i][3]) is int:
          self.images[i] = Image.merge('RGB', self.images[i][0:3])
        else:
          self.images[i] = Image.merge('RGBA', self.images[i])
    
  def parse_layerlen(self,layerlen):
    # layers structure
    (self.num_layers,) = self._readf(">h")
    if self.num_layers < 0:
      self.num_layers = -self.num_layers
      Logger.info(INDENT_OUTPUT(1, "First alpha is transparency for merged image"))
      self.header['mergedalpha'] = True
    Logger.info(INDENT_OUTPUT(1, "Layer info for %d layers:" % self.num_layers))
    if self.num_layers * (18 + 6 * self.header['channels']) > layerlen:
      raise ValueError("Unlikely number of %s layers for %s channels with %s layerlen. Giving up." % (self.num_layers, self.header['channels'], layerlen))
    linfo = [] # collect header infos here
    for i in range(self.num_layers):
      l = {}
      l['idx'] = i
      #
      # Layer Info
      #
      (l['top'], l['left'], l['bottom'], l['right'], l['channels']) = self._readf(">llllH")
      (l['rows'], l['cols']) = (l['bottom'] - l['top'], l['right'] - l['left'])
      Logger.info(INDENT_OUTPUT(1, "layer %(idx)d: (%(left)4d,%(top)4d,%(right)4d,%(bottom)4d), %(channels)d channels (%(cols)4d cols x %(rows)4d rows)" % l))
      # Sanity check
      if l['bottom'] < l['top'] or l['right'] < l['left'] or l['channels'] > 64:
        Logger.info(INDENT_OUTPUT(2, "Something's not right about that, trying to skip layer."))
        self.fd.seek(6 * l['channels'] + 12, 1) # 1: SEEK_CUR
        self._skip_block("layer info: extra data", 2)
        continue # next layer
      # Read channel infos
      l['chlengths'] = []
      l['chids']  = []
      # - 'hackish': addressing with -1 and -2 will wrap around to the two extra channels
      l['chindex'] = [ -1 ] * (l['channels'] + 2)
      for j in range(l['channels']):
        chid, chlen = self._readf(">hL")
        l['chids'].append(chid)
        l['chlengths'].append(chlen)
        Logger.info(INDENT_OUTPUT(3, "Channel %2d: id=%2d, %5d bytes" % (j, chid, chlen)))
        if -2 <= chid < l['channels']:
          # pythons negative list-indexs: [ 0, 1, 2, 3, ... -2, -1]
          l['chindex'][chid] = j
        else:
          Logger.info(INDENT_OUTPUT(3, "Unexpected channel id %d" % chid))
        l['chidstr'] = CHANNEL_SUFFIXES.get(chid, "?")
      # put channel info into connection
      linfo.append(l)
      l['blend_mode'] = self.parse_layer_blend_mode()
      # remember position for skipping unrecognized data
      (extralen,) = self._readf(">L")
      extrastart = self.fd.tell()

      l['mask'] = self.parse_layer_mask()
      self._skip_block("layer blending ranges", 3)
      #
      # Layer name
      #
      name_start = self.fd.tell()
      (l['namelen'],) = self._readf(">B")
      addl_layer_data_start = name_start + self._pad4(l['namelen'] + 1)
      # - "-1": one byte traling 0byte. "-1": one byte garble.
      # (l['name'],) = readf(f, ">%ds" % (self._pad4(1+l['namelen'])-2))
      (l['name'],) = self._readf(">%ds" % (l['namelen']))
      Logger.info(INDENT_OUTPUT(3, "Name: '%s'" % l['name']))
      self.fd.seek(addl_layer_data_start, 0)
      #
      # Read add'l Layer Information
      #
      while self.fd.tell() < extrastart + extralen:
        (signature, key, size, ) = self._readf(">4s4sL") # (n,) is a 1-tuple.
        Logger.info(INDENT_OUTPUT(3, "Addl info: sig='%s' key='%s' size='%d'" %
                      (signature, key, size)))
        next_addl_offset = self.fd.tell() + self._pad2(size)
        if key == 'luni':
          namelen = self._readf(">L")[0]
          l['name'] = u''
          for count in range(0, namelen):
            l['name'] += unichr(self._readf(">H")[0])
          Logger.info(INDENT_OUTPUT(4, u"Unicode Name: '%s'" % l['name']))
        elif key == 'TySh':
          version = self._readf(">H")[0]
          (xx, xy, yx, yy, tx, ty,) = self._readf(">dddddd") #transform
          text_version = self._readf(">H")[0]
          text_desc_version = self._readf(">L")[0]
          text_desc = self._read_descriptor()
          warp_version = self._readf(">H")[0]
          warp_desc_version = self._readf(">L")[0]
          warp_desc = self._read_descriptor()
          (left,top,right,bottom,) = self._readf(">llll")
          Logger.info(INDENT_OUTPUT(4, "ver=%d tver=%d dver=%d"
                 % (version, text_version, text_desc_version)))
          Logger.info(INDENT_OUTPUT(4, "%f %f %f %f %f %f" % (xx, xy, yx, yy, tx, ty,)))
          Logger.info(INDENT_OUTPUT(4, "l=%f t=%f r=%f b=%f"
                 % (left, top, right, bottom)))
          l['text_layer'] = {}
          l['text_layer']['text_desc'] = text_desc
          l['text_layer']['text_transform'] = (xx, xy, yx, yy, tx, ty,)
          l['text_layer']['left'] = left
          l['text_layer']['top'] = top
          l['text_layer']['right'] = right
          l['text_layer']['bottom'] = bottom
        self.fd.seek(next_addl_offset, 0)
      # Skip over any extra data
      self.fd.seek(extrastart + extralen, 0) # 0: SEEK_SET
      self.layers.append(l)
    self.merge_image(linfo);
  
  def parse_misclen(self):
    miscstart = self.fd.tell()
    # process layer info section
    (layerlen,) = self._readf(">L")
    if layerlen:
      self.parse_layerlen(layerlen)
    else:
      Logger.info(INDENT_OUTPUT(1, "Layer info section is empty"))
    skip = miscstart + misclen - self.fd.tell()
    if skip:
      Logger.info("")
      Logger.info("Skipped %d bytes at end of misc data?" % skip)
      self.fd.seek(skip, 1) # 1: SEEK_CUR
    
  def parse_layers_and_masks(self):
    if not self.header:
      self.parse_header()
    if not self.ressources:
      self._skip_block('image resources', new_line=True)
      self.ressources = 'not parsed'

    Logger.info("")
    Logger.info("# Layers & Masks #")

    self.layers = []
    self.images = []
    self.header['mergedalpha'] = False
    (misclen,) = self._readf(">L")
    if misclen:
      self.parse_misclen()
    else:
      Logger.info(INDENT_OUTPUT(1, "Misc info section is empty"))

