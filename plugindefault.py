# -*- coding: latin-1 -*-

from pluginmanager import SkidmarkCSSPlugin
from htmlcolors import HTMLColors

class PropertyDarken(SkidmarkCSSPlugin):
  def __init__(self):
    SkidmarkCSSPlugin.__init__(self, 'darken')
  
  def eval(self, *args):
    # We expect 1 to 2 params
    color, percent = (args + (None,))[:2]
    
    html_colors = HTMLColors()
    color = html_colors.get_color_shortest(color)
    
    if percent:
      if percent.endswith("%"):
        percent = percent[:-1]
      
      try:
        percent = int(percent)
      except:
        percent = 0
    
    if not percent:
      return html_colors.darken(color)
    
    return html_colors.darken(color, percent)

class PropertyLighten(SkidmarkCSSPlugin):
  def __init__(self):
    SkidmarkCSSPlugin.__init__(self, 'lighten')
  
  def eval(self, *args):
    # We expect 1 to 2 params
    color, percent = (args + (None,))[:2]
    
    html_colors = HTMLColors()
    color = html_colors.get_color_shortest(color)
    
    if percent:
      if percent.endswith("%"):
        percent = percent[:-1]
      
      try:
        percent = int(percent)
      except:
        percent = 0
    
    if not percent:
      return html_colors.lighten(color)
    
    return html_colors.lighten(color, percent)
