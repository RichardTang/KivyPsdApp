import kivy
kivy.require('1.0.6') # replace with your current kivy version !

from kivy.app import App
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.logger import Logger
    
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
    return self.label
    
  def prepare(self):
    self.message='xxxxxxx'
    Logger.info('xxxxxxxxxxtt')
    
  def addLog(self, inMsg):
    self.message= self.message + '\n' + inMsg
    self.label.text=self.message
    self.label.refresh()

    
if __name__ == '__main__':
  MyApp().run()

