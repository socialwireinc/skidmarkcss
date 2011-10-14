# -*- coding: latin-1 -*-

from pluginmanager import SkidmarkCSSPlugin, Color, Unit, pluginargs
from htmlcolors import HTMLColors

class PropertyDarken(SkidmarkCSSPlugin):
  def __init__(self):
    SkidmarkCSSPlugin.__init__(self, 'darken')
  
  @pluginargs(Color, Unit(25, type='%'))
  def eval(self, color, percent):
    color = HTMLColors.get_color_shortest(color.value)
    return HTMLColors.darken(color, int(percent.value or 0))

class PropertyLighten(SkidmarkCSSPlugin):
  def __init__(self):
    SkidmarkCSSPlugin.__init__(self, 'lighten')
  
  @pluginargs(Color, Unit(25, type='%'))
  def eval(self, color, percent):
    color = HTMLColors.get_color_shortest(color.value)
    return HTMLColors.lighten(color, int(percent.value or 0))
