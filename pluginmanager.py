# -*- coding: latin-1 -*-
import re

r_unit = re.compile(r"^\s*(\d+(?:\.\d*)?)(px|em|%|pt)?\s*$")

class PluginArg(object):
  def __init__(self, default=None):
    if default is not None and not isinstance(default, basestring):
      default = unicode(default)
    self.default_value = default
    self.value = None
  def validate(self, s):
    self.value = s
  def __str__(self):
    return self.value

class Unit(PluginArg):
  def __init__(self, default=None, type=None):
    self.default_type = type
    self.type = type
    super(Unit, self).__init__(default)
  def validate(self, s):
    mo = r_unit.match(s)
    if not mo: raise Exception("Not a unit: %s" % (s,))
    v,t = mo.groups()
    if self.default_type:
      if t is not None and self.default_type != t: raise Exception("Wrong unit: %s (expected %s)" % (t, self.type))
    else:
      self.type = t
    self.value = v
  def __str__(self):
    return "%s%s" % (self.value, self.type or '')

class String(PluginArg):
  pass

class Color(PluginArg):
  pass

def args(*params):
  params = list(params)
  for idx,p in enumerate(params):
    try:
      if not issubclass(p, PluginArg): raise Exception("Arguments must be subclasses of PluginArg")
      params[idx] = p()
    except:
      if not issubclass(p.__class__, PluginArg): raise Exception("Arguments must be subclasses of PluginArg")
      #TODO: if we pass a '1' for example, everything goes to hell
    
  def outer(func):
    def inner(self, *args):
      if len(args) > len(params): raise Exception("Too many arguments")
      newargs = []
      for idx,expected in enumerate(params):
        expected.validate(args[idx] if idx < len(args) else expected.default_value)
        newargs.append(expected)
      return func(self, *newargs)
    inner.__doc__ = func.__doc__
    inner.__name__ = func.__name__
    inner.params = params
    return inner
  return outer

class SkidmarkCSSPlugin(object):
  def __init__(self, name):
    self.name = name
    
  def eval(self, *args):
    raise Exception("eval method must be overwritten")

