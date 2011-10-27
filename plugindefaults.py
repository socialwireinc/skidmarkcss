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

class PropertyGradient(SkidmarkCSSPlugin):
  def __init__(self):
    SkidmarkCSSPlugin.__init__(self, 'gradient')

  def eval(self, direction, color_stop1, color_perc1, color_stop2, color_perc2, *args):
    # Validate the direction
    if direction == "vertical":
      direction_type = ( "top", "linear, left top, left bottom", "top", "top", "top", "top", 0, "linear" )
    elif direction == "horizontal":
      direction_type = ( "left", "linear, left top, right top", "left", "left", "left", "left", 1, "linear" )
    elif direction == "diag-down":
      direction_type = ( "-45deg", "linear, left top, right bottom", "-45deg", "-45deg", "-45deg", "-45deg", 1, "linear" )
    elif direction == "diag-up":
      direction_type = ( "45deg", "linear, left bottom, right top", "45deg", "45deg", "45deg", "45deg", 1, "linear" )
    elif direction == "radial":
      direction_type = ( "center, ellipse cover", "radial, center center 0%, center center 100%", "center, ellipse cover", "center, ellipse cover", "center, ellipse cover", "center, ellipse cover", 1, "radial" )
    else:
      direction_type = None
    
    if not direction_type:
      raise Exception("Invalid 'direction' for %s plugin, got '%s'" % ( self.name, direction ))
    
    # Assemble color stops
    color_stops = [
      (color_stop1, color_perc1),
      (color_stop2, color_perc2)
    ] + [ tuple(args[idx:idx + 2]) for idx in range(0, len(args), 2) ]
    
    if len(color_stops[-1]) == 1:
      color_stops[-1] = ( color_stops[-1][0], "100%" )
    
    # validate all the colors. If it doesn't raise, we're all good!
    for color, stop in color_stops:
      clr = Color()
      clr.validate(color)
    
    svg = ["""<?xml version="1.0" ?>"""]
    svg.append("""<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 1 1" preserveAspectRatio="none">""")
    svg.append("""<linearGradient id="grad-ucgg-generated" gradientUnits="userSpaceOnUse" x1="0%" y1="0%" x2="0%" y2="100%">""")
    
    for color, stop in color_stops:
      svg.append("""<stop offset="%s" stop-color="%s" stop-opacity="1"/>""" % ( stop, color ))
    
    svg.append("""</linearGradient>""")
    svg.append("""<rect x="0" y="0" width="1" height="1" fill="url(#grad-ucgg-generated)" />""")
    svg.append("""</svg>""")
    
    color_stops_style1 = ",".join([ "%s %s" % ( color, stop ) for color, stop in color_stops ])
    color_stops_style2 = ",".join([ "color-stop(%s,%s)" % ( stop, color ) for color, stop in color_stops ])
    
    properties = []
    properties.append("%s" % ( color_stop1, ))
    properties.append("url(data:image/svg+xml;base64,%s)" % ( ("\n".join(svg)).encode("base64").replace("\n", ""), ))
    properties.append("-moz-%s-gradient(%s, %s)" % ( direction_type[7], direction_type[0], color_stops_style1 ))
    properties.append("-webkit-gradient(%s, %s)" % ( direction_type[1], color_stops_style2 ))
    properties.append("-webkit-%s-gradient(%s, %s)" % ( direction_type[7], direction_type[2], color_stops_style1 ))
    properties.append("-o-%s-gradient(%s, %s)" % ( direction_type[7], direction_type[3], color_stops_style1 ))
    properties.append("-ms-%s-gradient(%s, %s)" % ( direction_type[7], direction_type[4], color_stops_style1 ))
    properties.append("%s-gradient(%s, %s)" % ( direction_type[7], direction_type[5], color_stops_style1 ))
    properties.append("filter: progid:DXImageTransform.Microsoft.gradient(startColorstr='%s',endColorstr='%s',GradientType=%s)" % ( color_stop1, color_stops[-1][0], direction_type[6] ))
    
    return properties

