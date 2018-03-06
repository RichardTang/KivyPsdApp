# coding:utf-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import kivy
kivy.require('1.0.6') # replace with your current kivy version !

from kivy.app import App
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.logger import Logger
import os
from psdparser import PSDParser
from kivy.uix.image import Image
from viewport import Viewport

class MyLabel(Label):
  def on_touch_down(self, touch, after=False):
    if after:
      print "Fired after the event has been dispatched!"
      Logger.info('after')
    else:
      Clock.schedule_once(lambda dt: self.on_touch_down(touch, True))
      Logger.info('before')
      return super(MyLabel, self).on_touch_down(touch)

class MyApp(App):
  message=''
  label = MyLabel(text='KivyPsdApp')
  psdParser=None
  
  def build(self):
    self.prepare()
    self.label.text = self.message
    #Clock.schedule_once(lambda dt: self.searchPsd())
    #self.searchPsd()
    #return self.label
    #self.psdParser.merged_image.save('mmm.png', 'PNG')
    #Logger.info('sss001')
    #img = Image(source='mmm.png')
    #Logger.info('sss002')
    #return img
    
  def prepare(self):
    self.message='xxxxxxx'
    Logger.info('xxxxxxxxxxtt')
    
  def addLog(self, inMsg):
    self.message= self.message + '\n' + inMsg
    self.label.text=self.message
    self.label.refresh()
    
  def searchPsd(self):
    Logger.info('searchPsd')
    Logger.info(os.getcwd())
    dirPath = os.getcwd()
    dirPath=os.path.join(dirPath,'..')
    destDir=os.path.join(dirPath,'002_home')
    dirs=os.listdir(destDir)
    for file in dirs:
      Logger.info(file)
      
    dirPath=os.path.join(dirPath,'..')
    dirPath=os.path.join(dirPath,'working')
    dirPath=os.path.join(dirPath,"小程序")
    dirs = os.listdir( dirPath )
    for file in dirs:
      Logger.info(file)
    psdFile = os.path.join(dirPath,'01首页-中国.psd')
    Logger.info('001')
    parser=PSDParser(psdFile)
    Logger.info('002')
    parser.parse()
    Logger.info('003')
    self.psdParser = parser
    pass
    
if __name__ == '__main__':
  MyApp().run()
