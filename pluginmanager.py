# -*- coding: latin-1 -*-

import inspect
import re

from htmlcolors import HTMLColors

r_unit = re.compile(r"^\s*(\d+(?:\.\d*)?)(px|em|%|pt)?\s*$")

class SkidmarkCSSPlugin(object):
  def __init__(self, name):
    self.name = name
    
  def eval(self, *args):
    raise Exception("eval method must be overwritten")

class PluginArg(object):
  def __init__(self, default=None, type=None):
    """Initialize the object"""
    
    # We need the default value to be a string. If it isn't, we need to convert it.
    if default is not None and not isinstance(default, basestring):
      default = unicode(default)
    
    self.default_type = type
    self.default_value = default
    self.value = None
  
  def validate(self, value):
    """Validate the object. Will set the value property when validated"""
    
    self.value = value
    return
  
  def __str__(self):
    """Object representation: self.value"""
    
    return self.value

class Unit(PluginArg):
  def __init__(self, default=None, type=None):
    self.type = type
    super(Unit, self).__init__(default, type)
  
  def validate(self, value):
    mo = r_unit.match(value)
    
    if not mo:
      raise Exception("Invalid Unit: %s" % ( value, ))
    
    mo_value, mo_type = mo.groups()
    
    if self.default_type:
      if mo_type is not None and self.default_type != mo_type:
        raise Exception("Incorrect Unit Type. Got %s, but expected %s" % ( mo_type, self.type ))
    else:
      self.type = mo_type
    self.value = mo_value
    
    return
  
  def __str__(self):
    return "%s%s" % ( self.value, self.type or "" )

class String(PluginArg):
  def __init__(self, default=None, type=None):
    self.type = type
    super(Unit, self).__init__(default, type)
  
  def validate(self, value):
    """String validator"""
    
    if not isinstance(value, basestring):
      raise Exception()
      
    return super(String, self).validate(value)    

class Color(PluginArg):
  def __init__(self, default=None, type=None):
    self.type = type
    super(Color, self).__init__(default, type)
  
  def validate(self, value):
    """Color validator"""
    
    is_valid = False
    if isinstance(value, basestring):
      if value.startswith("#"):
        rgb = HTMLColors.get_rgb(value) # will raise if the color is invalid
        is_valid = True
      else:
        # This must be a color name, see if we know about it!
        is_valid = HTMLColors.htmlcolors.has_key(value.lower())
    
    if not is_valid:
      raise Exception("%s is not a valid Color" % ( value, ))
    
    return super(Color, self).validate(value)    

def pluginargs(*params):
  """Decorator for SkidmarkCSS Plugin Arguments"""
  
  params = list(params)
  
  for idx, pluginarg in enumerate(params):
    invalid_param = False
    
    if inspect.isclass(pluginarg):
      if not issubclass(pluginarg, PluginArg):
        invalid_param = True
      else:
        params[idx] = pluginarg()
    else:
      if not isinstance(pluginarg, PluginArg):
        invalid_param = True
    
    if invalid_param:
      pluginarg_type = type(pluginarg) is type and pluginarg.__name__ or type(pluginarg).__name__
      raise Exception("Arguments must be subclasses of PluginArg. Got '%s'" % ( pluginarg_type, ))
  
  def outer(func):
    def inner(self, *args):
      if len(args) > len(params):
        raise Exception("Too many arguments")
      
      newargs = []      
      for idx, expected in enumerate(params):
        expected.validate(args[idx] if idx < len(args) else expected.default_value)
        newargs.append(expected)
      
      return func(self, *newargs)
    
    inner.__doc__ = func.__doc__
    inner.__name__ = func.__name__
    inner.params = params
    
    return inner
  return outer
