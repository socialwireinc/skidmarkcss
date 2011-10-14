# -*- coding: latin-1 -*-

from pluginmanager import SkidmarkCSSPlugin, args, Color, Unit
import pluginmanager
from htmlcolors import HTMLColors

class PropertyDarken(SkidmarkCSSPlugin):
  def __init__(self):
    SkidmarkCSSPlugin.__init__(self, 'darken')
  
  @args(Color, Unit(25, type='%'))
  def eval(self, color, percent):
    color = HTMLColors.get_color_shortest(color.value)
    return HTMLColors.darken(color, int(percent.value or 0))

class PropertyLighten(SkidmarkCSSPlugin):
  def __init__(self):
    SkidmarkCSSPlugin.__init__(self, 'lighten')
  
  @args(Color, Unit(25, type='%'))
  def eval(self, color, percent):
    color = HTMLColors.get_color_shortest(color.value)
    return HTMLColors.lighten(color, int(percent.value or 0))

