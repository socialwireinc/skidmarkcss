# -*- coding: latin-1 -*-

PROPERTY_SHORTHAND_TYPE_STANDARD4 = "standard4"
PROPERTY_SHORTHAND_TYPE_PASSTHRU = "passthru"
PROPERTY_SHORTHAND_TYPE_CUSTOM = "custom"

class ShorthandHandler(object):
  """This object contains classmethods that are responsible for determining
  and returning the shorthand version of properties if all the elements to
  be able to do so are present"""
  
  def __init__(self):
    pass
  
  @classmethod
  def is_shorthand(cls, prop_name):
    return PROPERTY_SHORTHANDS.has_key(prop_name)
  
  @classmethod
  def expand_shorthand(cls, prop_name, prop_value):
    properties = None
    
    blocks = PROPERTY_SHORTHANDS.get(prop_name)
    if blocks:
      for block in blocks:
        style = block[0]
        block_values = block[1:]
        
        if style == PROPERTY_SHORTHAND_TYPE_STANDARD4:
          properties = cls.expand_standard4(block_values, prop_value)
        elif style == PROPERTY_SHORTHAND_TYPE_PASSTHRU:
          properties = cls.expand_passthru(block_values, prop_value)
        elif style == PROPERTY_SHORTHAND_TYPE_CUSTOM:
          fn_name = "expand_%s" % ( prop_name.replace("-", "_"), )
          if hasattr(cls, fn_name):
            properties = getattr(cls, fn_name)(block_values, prop_value)
    
    return properties
  
  @classmethod
  def get_all_expand_properties(cls, prop_name):
    properties = set()
    
    blocks = PROPERTY_SHORTHANDS.get(prop_name)
    if blocks:
      for block in blocks:
        style = block[0]
        block_values = block[1:]
        for value in block_values:
          properties.add(value)
    
    return list(properties)
  
  
  #
  # Processors: From long to short
  #
  
  @classmethod
  def process(cls, style, shorthand, block_values):
    """Process a style, given the shorhand and block values. The block values
    are the fields, present in the declaration block's properties that match
    the property names found in the PROPERTY_SHORTHANDS list."""
    
    shorthand_property = ""
    
    if None not in block_values:
      if style == PROPERTY_SHORTHAND_TYPE_STANDARD4:
        shorthand_property = cls.process_standard4(shorthand, block_values)
      elif style == PROPERTY_SHORTHAND_TYPE_PASSTHRU:
        shorthand_property = cls.process_passthru(shorthand, block_values)
      elif style == PROPERTY_SHORTHAND_TYPE_CUSTOM:
        fn_name = "process_%s" % ( shorthand.replace("-", "_"), )
        if hasattr(cls, fn_name):
          shorthand_property = getattr(cls, fn_name)(shorthand, block_values)
    
    return shorthand_property or ""
  
  @classmethod
  def process_standard4(cls, shorthand, block_values):
    """This is the generic handler for the elements that require 4 params
    that are defined as 'top right bottom left', such as padding and margin."""
    
    if len(set(block_values)) == 1:
      shorthand_property = shorthand + ": " + block_values[0]
    elif block_values[0] == block_values[2] and block_values[1] == block_values[3]:
      shorthand_property = shorthand + ": " + " ".join(block_values[:2])
    elif block_values[1] == block_values[3]:
      shorthand_property = shorthand + ": " + " ".join(block_values[:3])
    else:
      shorthand_property = shorthand + ": " + " ".join(block_values)
    
    return shorthand_property
  
  @classmethod
  def process_passthru(cls, shorthand, block_values):
    """This is the generic handler for shorthands that are composed entirely of
    the property data defined in PROPERTY_SHORTHANDS, in the exact order."""
    
    return shorthand + ": " + " ".join(block_values)
  
  @classmethod
  def process_font(cls, shorthand, block_values):
    """Custom handler for the 'font' shorthand"""
    
    shorthand_property = None
    if len(block_values) == 5:
      shorthand_property = "%s: %s/%s %s %s %s" % tuple([shorthand] + block_values)
    elif len(block_values) == 6:
      shorthand_property = "%s: %s %s %s %s/%s %s" % tuple([shorthand] + block_values)
    
    return shorthand_property
  
  #
  # expanders: from short to long
  #
  
  @classmethod
  def expand_passthru(cls, block_values, prop_value):
    values = prop_value.split(" ", len(block_values))
    if len(block_values) == len(values):
      return zip(block_values, values)
    return None
  
  @classmethod
  def expand_standard4(cls, block_values, prop_value):
    #print prop_value, block_values
    return None


PROPERTY_EXPANDABLES = {
  #
  # border-radius
  #
  "border-radius": [
    "-moz-border-radius",
    "-webkit-border-radius"
  ],
  "border-top-left-radius": [
    "-moz-border-radius-topleft",
    "-webkit-border-top-left-radius"
  ],
  "border-top-right-radius": [
    "-moz-border-radius-topright",
    "-webkit-border-top-right-radius"
  ],
  "border-bottom-left-radius": [
    "-moz-border-radius-bottomleft",
    "-webkit-border-bottom-left-radius"
  ],
  "border-bottom-right-radius": [
    "-moz-border-radius-bottomright",
    "-webkit-border-bottom-right-radius"
  ]
}

PROPERTY_SHORTHANDS = {
  "padding": [
    [ PROPERTY_SHORTHAND_TYPE_STANDARD4,
      "padding-top", "padding-right", "padding-bottom", "padding-left" ],
  ],
  
  "margin": [
    [ PROPERTY_SHORTHAND_TYPE_STANDARD4,
      "margin-top", "margin-right", "margin-bottom", "margin-left" ],
  ],
  
  "border-width": [
    [ PROPERTY_SHORTHAND_TYPE_STANDARD4,
      "border-top-width", "border-right-width", "border-bottom-width", "border-left-width" ],
  ],
  
  "border-style": [
    [ PROPERTY_SHORTHAND_TYPE_STANDARD4,
      "border-top-style", "border-right-style", "border-bottom-style", "border-left-style" ],
  ],
  
  "border-color": [
    [ PROPERTY_SHORTHAND_TYPE_STANDARD4,
      "border-top-color", "border-right-color", "border-bottom-color", "border-left-color" ],
  ],
  
  "border": [
    [ PROPERTY_SHORTHAND_TYPE_PASSTHRU,
      "border-width", "border-style", "border-color" ]
  ],
  
  "border-top": [
    [ PROPERTY_SHORTHAND_TYPE_PASSTHRU,
      "border-top-width", "border-top-color", "border-top-style" ]
  ],
  
  "border-right": [
    [ PROPERTY_SHORTHAND_TYPE_PASSTHRU,
      "border-right-width", "border-right-color", "border-right-style" ]
  ],
  
  "border-bottom": [
    [ PROPERTY_SHORTHAND_TYPE_PASSTHRU,
      "border-bottom-width", "border-bottom-color", "border-bottom-style" ]
  ],
  
  "border-left": [
    [ PROPERTY_SHORTHAND_TYPE_PASSTHRU,
      "border-left-width", "border-left-color", "border-left-style" ]
  ],
  
  "font": [
    [ PROPERTY_SHORTHAND_TYPE_CUSTOM,
      "font-weight", "font-style", "font-variant", "font-size", "line-height", "font-family" ],
      
    [ PROPERTY_SHORTHAND_TYPE_CUSTOM,
      "font-size", "line-height", "font-weight", "font-style", "font-family" ],
  ],
  
  "background": [
    [ PROPERTY_SHORTHAND_TYPE_PASSTHRU,
      "background-color", "background-image", "background-repeat", "background-position" ],
  ],
  
  "list-style": [
    [ PROPERTY_SHORTHAND_TYPE_PASSTHRU,
      "list-style-type", "list-style-position", "list-style-image" ]
  ],
}

# Create a reverse mapping
PROPERTIES_AVAILABLE_FOR_SHORTHAND = []
for block_lists in PROPERTY_SHORTHANDS.values():
  for block in block_lists:
    PROPERTIES_AVAILABLE_FOR_SHORTHAND.extend(block[1:])
PROPERTIES_AVAILABLE_FOR_SHORTHAND = list(set(PROPERTIES_AVAILABLE_FOR_SHORTHAND))

