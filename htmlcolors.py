# -*- coding: latin-1 -*-

"""Defines the HTML colour names along with their values"""

class InvalidColorException(Exception):
  pass

class HTMLColors(object):
  htmlcolors = {
    'aliceblue': '#F0F8FF',
    'antiquewhite': '#FAEBD7',
    'aqua': '#00FFFF',
    'aquamarine': '#7FFFD4',
    'azure': '#F0FFFF',
    'beige': '#F5F5DC',
    'bisque': '#FFE4C4',
    'black': '#000000',
    'blanchedalmond': '#FFEBCD',
    'blue': '#0000FF',
    'blueviolet': '#8A2BE2',
    'brown': '#A52A2A',
    'burlywood': '#DEB887',
    'cadetblue': '#5F9EA0',
    'chartreuse': '#7FFF00',
    'chocolate': '#D2691E',
    'coral': '#FF7F50',
    'cornflowerblue': '#6495ED',
    'cornsilk': '#FFF8DC',
    'crimson': '#DC143C',
    'cyan': '#00FFFF',
    'darkblue': '#00008B',
    'darkcyan': '#008B8B',
    'darkgoldenrod': '#B8860B',
    'darkgray': '#A9A9A9',
    'darkgreen': '#006400',
    'darkgrey': '#A9A9A9',
    'darkkhaki': '#BDB76B',
    'darkmagenta': '#8B008B',
    'darkolivegreen': '#556B2F',
    'darkorange': '#FF8C00',
    'darkorchid': '#9932CC',
    'darkred': '#8B0000',
    'darksalmon': '#E9967A',
    'darkseagreen': '#8FBC8F',
    'darkslateblue': '#483D8B',
    'darkslategray': '#2F4F4F',
    'darkslategrey': '#2F4F4F',
    'darkturquoise': '#00CED1',
    'darkviolet': '#9400D3',
    'deeppink': '#FF1493',
    'deepskyblue': '#00BFFF',
    'dimgray': '#696969',
    'dimgrey': '#696969',
    'dodgerblue': '#1E90FF',
    'firebrick': '#B22222',
    'floralwhite': '#FFFAF0',
    'forestgreen': '#228B22',
    'fuchsia': '#FF00FF',
    'gainsboro': '#DCDCDC',
    'ghostwhite': '#F8F8FF',
    'gold': '#FFD700',
    'goldenrod': '#DAA520',
    'gray': '#808080',
    'green': '#008000',
    'greenyellow': '#ADFF2F',
    'grey': '#808080',
    'honeydew': '#F0FFF0',
    'hotpink': '#FF69B4',
    'indianred': '#CD5C5C',
    'indigo': '#4B0082',
    'ivory': '#FFFFF0',
    'khaki': '#F0E68C',
    'lavender': '#E6E6FA',
    'lavenderblush': '#FFF0F5',
    'lawngreen': '#7CFC00',
    'lemonchiffon': '#FFFACD',
    'lightblue': '#ADD8E6',
    'lightcoral': '#F08080',
    'lightcyan': '#E0FFFF',
    'lightgoldenrodyellow': '#FAFAD2',
    'lightgray': '#D3D3D3',
    'lightgreen': '#90EE90',
    'lightgrey': '#D3D3D3',
    'lightpink': '#FFB6C1',
    'lightsalmon': '#FFA07A',
    'lightseagreen': '#20B2AA',
    'lightskyblue': '#87CEFA',
    'lightslategray': '#778899',
    'lightslategrey': '#778899',
    'lightsteelblue': '#B0C4DE',
    'lightyellow': '#FFFFE0',
    'lime': '#00FF00',
    'limegreen': '#32CD32',
    'linen': '#FAF0E6',
    'magenta': '#FF00FF',
    'maroon': '#800000',
    'mediumaquamarine': '#66CDAA',
    'mediumblue': '#0000CD',
    'mediumorchid': '#BA55D3',
    'mediumpurple': '#9370D8',
    'mediumseagreen': '#3CB371',
    'mediumslateblue': '#7B68EE',
    'mediumspringgreen': '#00FA9A',
    'mediumturquoise': '#48D1CC',
    'mediumvioletred': '#C71585',
    'midnightblue': '#191970',
    'mintcream': '#F5FFFA',
    'mistyrose': '#FFE4E1',
    'moccasin': '#FFE4B5',
    'navajowhite': '#FFDEAD',
    'navy': '#000080',
    'oldlace': '#FDF5E6',
    'olive': '#808000',
    'olivedrab': '#6B8E23',
    'orange': '#FFA500',
    'orangered': '#FF4500',
    'orchid': '#DA70D6',
    'palegoldenrod': '#EEE8AA',
    'palegreen': '#98FB98',
    'paleturquoise': '#AFEEEE',
    'palevioletred': '#D87093',
    'papayawhip': '#FFEFD5',
    'peachpuff': '#FFDAB9',
    'peru': '#CD853F',
    'pink': '#FFC0CB',
    'plum': '#DDA0DD',
    'powderblue': '#B0E0E6',
    'purple': '#800080',
    'red': '#FF0000',
    'rosybrown': '#BC8F8F',
    'royalblue': '#4169E1',
    'saddlebrown': '#8B4513',
    'salmon': '#FA8072',
    'sandybrown': '#F4A460',
    'seagreen': '#2E8B57',
    'seashell': '#FFF5EE',
    'sienna': '#A0522D',
    'silver': '#C0C0C0',
    'skyblue': '#87CEEB',
    'slateblue': '#6A5ACD',
    'slategray': '#708090',
    'slategrey': '#708090',
    'snow': '#FFFAFA',
    'springgreen': '#00FF7F',
    'steelblue': '#4682B4',
    'tan': '#D2B48C',
    'teal': '#008080',
    'thistle': '#D8BFD8',
    'tomato': '#FF6347',
    'turquoise': '#40E0D0',
    'violet': '#EE82EE',
    'wheat': '#F5DEB3',
    'white': '#FFFFFF',
    'whitesmoke': '#F5F5F5',
    'yellow': '#FFFF00',
    'yellowgreen': '#9ACD32'
  }

  @classmethod
  def get_color_name(cls, color_value):
    """Returns the color name matching this value. Returns an empty string
    if no suitable match is found"""
    
    if isinstance(color_value, basestring):
      value = color_value.upper()
      
      for col, val in HTMLColors.htmlcolors.iteritems():
        if val == value:
          return col
    
    return ""

  @classmethod
  def get_color_value(cls, color_name):
    """Returns the color value mathing this name. Returns an empty string
    if no suitable match is found"""
    
    if isinstance(color_name, basestring):
      color = color_name.lower()
      
      if color in HTMLColors.htmlcolors:
        return HTMLColors.htmlcolors[color]
    
    return ""

  @classmethod
  def get_color_shortest(cls, color_name_or_value):
    """Attempts to retrieve by name and value and returns the shortest
    string. Returns the input string if nothing is found"""
    
    name = cls.get_color_name(color_name_or_value) or color_name_or_value
    value = cls.get_color_value(color_name_or_value) or color_name_or_value
    
    if value:
      if len(value) == 7:
        condensed = [ value[v] for v in range(1, 7, 2) if value[v] == value[v + 1] ]
        if len(condensed) == 3:
          value = "#" + "".join(condensed)
    
    l_name = len(name)
    l_value = len(value)
    
    if l_name == l_value:
      return color_name_or_value
    
    if (l_name and not l_value) or (name and l_value and l_name < l_value):
      return name
    
    if (l_value and not l_name) or (value and l_name and l_value < l_name):
      return value
    
    return color_name_or_value

  @classmethod
  def is_valid_color_value(cls, color_value):
    """Validates the characters, not the format"""
    
    c_value = color_value.strip().lower()
    
    if c_value and c_value.startswith("#"):
      c_value = c_value[1:]
    
    if not c_value:
      return False
    
    chars = "abcdef0123456789"
    invalid = [ c for c in c_value if chars.find(c) == -1 ]
    
    return not invalid
  
  @classmethod
  def get_rgb(cls, color):
    if not color.startswith("#"):
      # Are we passing a color, if this doens't work, we can't do anything!
      c_value = cls.get_color_value(color)
      if c_value:
        color = c_value
    
    if cls.is_valid_color_value(color):
    
      if len(color) in (4, 7):
        c_value = color[1:]
        
        if len(c_value) == 3:
          r, g, b = [ int(hex, 16) for hex in [ c_value[cnt:cnt + 1] * 2 for cnt in range(3) ] ]
        else:
          r, g, b = [ int(hex, 16) for hex in [ c_value[cnt * 2:cnt * 2 + 2] for cnt in range(3) ] ]
        return r, g, b
    
    raise InvalidColorException("%s is not a valid color" % ( color, ))
  
  @classmethod
  def get_color_from_rgb(cls, r, g, b):
    """Return an html color from rgb"""
    
    value = "#" + "".join([ ("0" + hex(i)[2:])[-2:] for i in (r, g, b) ])
    return cls.get_color_shortest(value)

  @classmethod
  def lighten(cls, color, percentage=25):
    """Lightens a HTML color by the percentage specified"""
    
    r, g, b = cls.get_rgb(color)
    
    if percentage:
      r, g, b = [ int(i + (percentage * (255 - i + 1) / 100.0)) for i in (r, g, b) ]
    
    return cls.get_color_from_rgb(r, g, b)

  @classmethod
  def darken(cls, color, percentage=25):
    """Darkens a HTML colour by the percentage specified"""
    
    r, g, b = cls.get_rgb(color)
    
    if percentage:
      r, g, b = [ int(i - (percentage * i / 100.0)) for i in (r, g, b) ]
    
    return cls.get_color_from_rgb(r, g, b)
