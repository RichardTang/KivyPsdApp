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
  
  def build(self):
    self.prepare()
    self.label.text = self.message
    Clock.schedule_once(lambda dt: self.searchPsd())
    return self.label
    
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
    dirPath=os.path.join(dirPath,'..')
    dirPath=os.path.join(dirPath,'working')
    dirPath=os.path.join(dirPath,"小程序")
    dirs = os.listdir( dirPath )
    for file in dirs:
      Logger.info(file)
    pass
    
if __name__ == '__main__':
  MyApp().run()
