# -*- coding: latin-1 -*-

class SkidmarkCSSPlugin(object):
  def __init__(self, name):
    self.name = name
    
  def eval(self, *args):
    raise Exception("eval method must be overwritten")
