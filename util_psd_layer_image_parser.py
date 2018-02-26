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
from util_psd_image_resource_parser import PsdImageResourceParser

class PsdLayerImageParser(PsdImageResourceParser):
  def _unicode_string(self):
    len = self._readf(">L")[0]
    result = u''
    for count in range(len):
      val = self._readf(">H")[0]
      if val:
        result += unichr(val)
    return result
    
  def _desc_TEXT(self):
    return self._unicode_string()

  def _desc_enum(self):
    return { 
      'typeID' : self._string_or_key(),
        'enum' : self._string_or_key(),
           }

  def _desc_long(self):
    return self._readf(">l")[0]

  def _desc_bool(self):
    return self._readf(">?")[0]

  def _desc_doub(self):
    return self._readf(">d")[0]

  def _desc_untf(self):
    untf = {}
    untf['desc'] = self._readf(">4s")[0]
    untf['value'] = self._readf(">d")[0]
    return untf

  def _string_or_key(self):
    len = self._readf(">L")[0]
    if not len:
      len = 4
    return self._readf(">%ds" % len)[0]

  def _desc_tdta(self):
    # Apparently it is pdf data?
    # http://telegraphics.com.au/svn/psdparse
    # descriptor.c pdf.c
    len = self._readf(">L")[0]
    Logger.info('len=%d' % len)
    pdf_data = self.fd.read(len)
    return pdf_data
    
  def _read_descriptor(self):
    # Descriptor
    _desc_item_factory = {
      'TEXT' : self._desc_TEXT,
      'enum' : self._desc_enum,
      'long' : self._desc_long,
      'bool' : self._desc_bool,
      'doub' : self._desc_doub,
      'UntF' : self._desc_untf,
      'tdta' : self._desc_tdta,
      'Objc' : self._read_descriptor,
    }

    class_id_name = self._unicode_string()
    class_id = self._string_or_key()
    Logger.info(INDENT_OUTPUT(4, u"name='%s' clsid='%s'" % (class_id_name, class_id)))

    item_count = self._readf(">L")[0]
    #Logger.info(INDENT_OUTPUT(4, "item_count=%d" % (item_count)))
    items = {}
    for item_index in range(item_count):
      item_key = self._string_or_key()
      item_type = self._readf(">4s")[0]
      if not item_type in _desc_item_factory:
        Logger.info(INDENT_OUTPUT(4, "unknown descriptor item '%s', skipping ahead." % item_type))
        break

      Logger.info('%s for %s' % (item_type, item_key))
      items[item_key] = _desc_item_factory[item_type]()
      Logger.info('%s done %s' % (item_type, item_key))
      #Logger.info(INDENT_OUTPUT(4, "item['%s']='%r'" % (item_key,items[item_key])))
      #print items[item_key]
    return items