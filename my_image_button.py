from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.graphics import BorderImage


class MyImageButton(ToggleButtonBehavior, BorderImage):
  def __init__(self, **kwargs):
    super(MyImageButton, self).__init__(**kwargs)
    #self.source = 'atlas://data/images/defaulttheme/checkbox_off'

  def on_state(self, widget, value):
    if value == 'down':
      #self.source = 'atlas://data/images/defaulttheme/checkbox_on'
      #border=(1,1,1,1)
      pass
    else:
      #self.source = 'atlas://data/images/defaulttheme/checkbox_off'
      #border=(0,0,0,0)
      pass

