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
    images = None
    merged_image = None

    def __init__(self, filename):
        self.filename = filename

    def parse(self):
        Logger.info("Opening '%s'" % self.filename)

        self.fd = open(self.filename, 'rb')
        try:
            self.parse_header()
            self.parse_image_resources()
            #self.parse_layers_and_masks()
            #self.parse_image_data()
        finally:
            self.fd.close()

        Logger.info("")
        Logger.info("DONE")



    def parse_image(self, li, is_layer=True):
        def parse_channel(li, idx, count, rows, cols, depth):
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
                Logger.info(INDENT_OUTPUT(1, "Handling RLE compressed data"))
                rlecounts = 2 * count * rows
                if chlen and chlen < rlecounts:
                    raise ValueError("Channel too short for RLE row counts (need %d bytes, have %d bytes)" % (rlecounts,chlen))
                pos += rlecounts # image data starts after RLE counts
                rlecounts_data = self._readf(">%dH" % (count * rows))
                for ch in range(count):
                    rlelen_for_channel = sum(rlecounts_data[ch * rows:(ch + 1) * rows])
                    data = self.fd.read(rlelen_for_channel)
                    channel_name = CHANNEL_SUFFIXES[li['chids'][idx]]
                    if li['channels'] == 2 and channel_name == 'B': channel_name = 'L'
                    p = Image.fromstring("L", (cols, rows), data, "packbits", "L" )
                    if is_layer:
                        if channel_name in PIL_BANDS:
                            self.images[li['idx']][PIL_BANDS[channel_name]] = p
                    else:
                        self.merged_image.append(p)

            elif COMPRESSIONS.get(comp) == 'Raw':
                Logger.info(INDENT_OUTPUT(1, "Handling Raw compressed data"))

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

            if (chlen is not None) and (self.fd.tell() != chpos + 2 + chlen):
                Logger.info("currentpos:%d should be:%d!" % (f.tell(), chpos + 2 + chlen))
                self.fd.seek(chpos + 2 + chlen, 0) # 0: SEEK_SET

            return

        if not self.header:
            self.parse_header()
        if not self.ressources:
            self._skip_block("image resources", new_line=True)
            self.ressources = 'not parsed'

        Logger.info("")
        Logger.info("# Image: %s/%d #" % (li['name'], li['channels']))

        # channels
        if is_layer:
            for ch in range(li['channels']):
                parse_channel(li, ch, 1, li['rows'], li['cols'], self.header['depth'])
        else:
            parse_channel(li, 0, li['channels'], li['rows'], li['cols'], self.header['depth'])
        return

    def _read_descriptor(self):
        # Descriptor
        def _unicode_string():
            len = self._readf(">L")[0]
            result = u''
            for count in range(len):
                val = self._readf(">H")[0]
                if val:
                    result += unichr(val)
            return result

        def _string_or_key():
            len = self._readf(">L")[0]
            if not len:
                len = 4
            return self._readf(">%ds" % len)[0]

        def _desc_TEXT():
            return _unicode_string()

        def _desc_enum():
            return { 'typeID' : _string_or_key(),
                     'enum' : _string_or_key(),
                     }

        def _desc_long():
            return self._readf(">l")[0]

        def _desc_bool():
            return self._readf(">?")[0]

        def _desc_doub():
            return self._readf(">d")[0]

        def _desc_tdta():
            # Apparently it is pdf data?
            # http://telegraphics.com.au/svn/psdparse
            # descriptor.c pdf.c

            len = self._readf(">L")[0]
            pdf_data = self.fd.read(len)
            return pdf_data

        _desc_item_factory = {
            'TEXT' : _desc_TEXT,
            'enum' : _desc_enum,
            'long' : _desc_long,
            'bool' : _desc_bool,
            'doub' : _desc_doub,
            'tdta' : _desc_tdta,
            'Objc' : _desc_tdta,#TODO:
            }

        class_id_name = _unicode_string()
        class_id = _string_or_key()
        Logger.info(INDENT_OUTPUT(4, u"name='%s' clsid='%s'" % (class_id_name, class_id)))

        item_count = self._readf(">L")[0]
        #Logger.info(INDENT_OUTPUT(4, "item_count=%d" % (item_count)))
        items = {}
        for item_index in range(item_count):
            item_key = _string_or_key()
            item_type = self._readf(">4s")[0]
            if not item_type in _desc_item_factory:
                Logger.info(INDENT_OUTPUT(4, "unknown descriptor item '%s', skipping ahead." % item_type))
                break

            items[item_key] = _desc_item_factory[item_type]()
            #Logger.info(INDENT_OUTPUT(4, "item['%s']='%r'" % (item_key,items[item_key])))
            #print items[item_key]
        return items

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

