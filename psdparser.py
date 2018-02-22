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
from util_psd_image_resource_parser import PsdImageResourceParser


class PSDParser(PsdImageResourceParser):

    ressources = None
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
            #pass
            #self.parse_image_resources()
            #self.parse_layers_and_masks()
            #self.parse_image_data()
        finally:
            self.fd.close()

        Logger.info("")
        Logger.info("DONE")

    def parse_image_resources(self):


        Logger.info("")
        Logger.info("# Ressources #")
        self.ressources = []
        (n,) = self._readf(">L") # (n,) is a 1-tuple.
        while n > 0:
            n -= self.parse_irb()
        if n != 0:
            Logger.info("Image resources overran expected size by %d bytes" % (-n))

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
            miscstart = self.fd.tell()
            # process layer info section
            (layerlen,) = self._readf(">L")
            if layerlen:
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

                    #
                    # Blend mode
                    #
                    bm = {}

                    (bm['sig'], bm['key'], bm['opacity'], bm['clipping'], bm['flags'], bm['filler'],
                     ) = self._readf(">4s4sBBBB")
                    bm['opacp'] = (bm['opacity'] * 100 + 127) / 255
                    bm['clipname'] = bm['clipping'] and "non-base" or "base"
                    bm['blending'] = BLENDINGS.get(bm['key'])
                    l['blend_mode'] = bm

                    Logger.info(INDENT_OUTPUT(3, "Blending mode: sig=%(sig)s key=%(key)s opacity=%(opacity)d(%(opacp)d%%) clipping=%(clipping)d(%(clipname)s) flags=%(flags)x" % bm))

                    # remember position for skipping unrecognized data
                    (extralen,) = self._readf(">L")
                    extrastart = self.fd.tell()

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
                    l['mask'] = m

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

                for i in range(self.num_layers):
                    # Empty layer
                    if linfo[i]['rows'] * linfo[i]['cols'] == 0:
                        self.images.append(None)
                        self.parse_image(linfo[i], is_layer=True)
                        continue

                    self.images.append([0, 0, 0, 0])
                    self.parse_image(linfo[i], is_layer=True)
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

            else:
                Logger.info(INDENT_OUTPUT(1, "Layer info section is empty"))

            skip = miscstart + misclen - self.fd.tell()
            if skip:
                Logger.info("")
                Logger.info("Skipped %d bytes at end of misc data?" % skip)
                self.fd.seek(skip, 1) # 1: SEEK_CUR
        else:
            Logger.info(INDENT_OUTPUT(1, "Misc info section is empty"))

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

