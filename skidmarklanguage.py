# -*- coding: latin-1 -*-

import re

ZERO_OR_ONE = 0
ZERO_OR_MORE = -1
ONE_OR_MORE = -2

p = lambda _:"("+_+")"
t_nl = "\n|\r\n|\r|\f"
t_nonascii = "[^\x00-\x9f]"
t_unicode = r"\\[0-9A-Fa-f]{1,6}(\r\n|[ \r\n\t\f])?"
t_escape = p(t_unicode) + r"|\\[^\n\r\f0-9a-fA-F]"
t_string1 = '"([^\n\r\f\"]|' + p(t_nl) + '|' + p(t_escape) + ')*"'
t_string2 = "'([^\n\r\f\']|" + p(t_nl) + "|" + p(t_escape) + ")*'"
t_string = p(t_string1) + "|" + p(t_string2)
t_nmstart = "\@font-face|&|[_A-Za-z]|" + p(t_nonascii) + "|" + p(t_escape)
t_nmchar = "[_A-Za-z0-9-]|" + p(t_nonascii) + "|" + p(t_escape)
t_name = p(t_nmchar) + "+"
t_hash = "#" + t_name
t_ident = "[-]?" + p(t_nmstart) + p(t_nmchar) + "*"
t_class = "\\." + t_ident

rec = re.compile

def template():
  return "@@template ", function(), declarationblock
  
def use():
  return "@@use ", function(), ";"
  
def import_rule():
  return rec("\@import\s+url\s*[^;]*;")

def hash():
  return rec(t_hash)

def string():
  return rec(t_string)

def ident():
  return rec(t_ident)

def class_():
  return rec(t_class)

def element_name():
  return rec(p(t_ident) + "|\\*")

def function():
  return ident(), "(", ZERO_OR_ONE, param_list(), ")"

def param_list():
  return ZERO_OR_ONE, param, ZERO_OR_MORE, (",", param)
  
def param():
  # FIX: Parameters may be within quotes
  # (if the case where a comma needs to be in the text)
  return rec(r"[^,)]*")

def comment():
  return rec(r"/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/")

def pseudo():
  return ":", [ function, ident ]

def css3pseudo():
  return ":", pseudo()

def attrib():
  return "[", ident, ZERO_OR_ONE, (attrib_type, [ ident, string ]), "]"

def attrib_type():
  return rec("~?=")
  
def simple_selector():
  return [ (element_name, ZERO_OR_MORE, [hash, class_, attrib, pseudo, css3pseudo]), (ONE_OR_MORE, [hash, class_, attrib, pseudo, css3pseudo]) ]

def combinator():
  return [ rec('[+>]') ]

def selector():
  return simple_selector(), ZERO_OR_ONE, (ZERO_OR_ONE, combinator, selector)

def expansion():
  return propertyname(), "{", declarationblock(), "}"

def directive():
  return "@", function(), ";"

def full_selector():
  return selector, ZERO_OR_MORE, (',',  selector )

def propertyname():
  return rec(t_name)

def propertyvalue():
  return re.compile(r"[^;}]*")

def property():
  return property_unterminated(), ";"
  
def property_unterminated():
  return propertyname, ":", propertyvalue

def declarationblock():
  return "{", ZERO_OR_MORE, [ property, directive, comment, declaration, use, expansion ], ZERO_OR_ONE, property_unterminated, "}"

def declaration():
  return full_selector(), declarationblock
  
def language():
  return ZERO_OR_MORE, [ import_rule, declaration, directive, comment, template ]

