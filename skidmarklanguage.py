# -*- coding: latin-1 -*-

"""The pyPEG language that defines SkidmarkCSS"""

import re

# pyPEG-specific
ZERO_OR_ONE = 0
ZERO_OR_MORE = -1
ONE_OR_MORE = -2

# RegExp Definitions
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
t_variable = "\$[_A-Za-z0-9]+"
t_constant = "[^ \n\r();,*/+-]+"
t_mathconstant = "\d[^ \n\r();,*/+-]*"
t_import_rule = "\@import\s+url\s*[^;]*;"
t_charset_rule = "\@charset\s+[^;]*;"
t_math = "(\*|\/|\+|\-){1}"
t_comment = r"/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/"
t_param = "[a-zA-Z0-9#.]+%?|" + t_string + "|" + t_variable

# Compiled RegExp
rec = re.compile
re_attrib_type = rec("~?=")
re_class = rec(t_class)
re_combinator = rec("[+>]")
re_comment = rec(t_comment)
re_constant = rec(t_constant)
re_mathconstant = rec(t_mathconstant)
re_element_name = rec(p(t_ident) + "|\\*")
re_hash = rec(t_hash)
re_ident = rec(t_ident)
re_import_rule = rec(t_import_rule)
re_charset_rule = rec(t_charset_rule)
re_math = rec(t_math)
re_name = rec(t_name)
re_param = rec(t_param)
re_propertyvalue = rec(r"[^;}]*")
re_string = rec(t_string)
re_variable = rec(t_variable)
re_property_value_start = re.compile("[a-zA-Z0-9_:#=().,-]+")
re_simple_property = re.compile("[a-zA-Z0-9]+")
re_css_func = re.compile("[a-zA-Z0-9-]+\([^\(]+(\([^\(\)]+?\)[^\(]+)*[^\)]+\)\)|[a-zA-Z0-9-]+\([^)]*\)")


def import_rule():
  return re_import_rule

def charset_rule():
  return re_charset_rule

def builtin_css_directives():
  return [ import_rule, charset_rule ]

def variable_set():
  return variable(), "=", [ math_operation, plugin, constant, variable ], ";"

def variable():
  return re_variable

def constant():
  return re_constant

def mathconstant():
  return re_mathconstant

def math_operation():
  return "(", [ math_var(), math_group ], math_op(), [ math_var(), math_group ], ZERO_OR_MORE, (math_op(), [ math_var(), math_group ]), ")"

def math_var():
  return [ mathconstant, variable ]

def math_group():
  return "(", math_operation(), ")"

def math_op():
  return re_math

def template():
  return "@@template ", function_declaration(), declarationblock
  
def use():
  return "@@use ", function(), ";"
  
def hash():
  return re_hash

def string():
  return re_string

def ident():
  return re_ident

def class_():
  return re_class

def element_name():
  return re_element_name

def function():
  return ident(), "(", ZERO_OR_ONE, param_list(), ")"

def param_list():
  return ZERO_OR_ONE, arg(), ZERO_OR_MORE, (",", arg())
  
def arg():
  return [ plugin, variable, string, math_operation, param ]
  
def function_declaration():
  return ident(), "(", ZERO_OR_ONE, param_list_declaration(), ")"

def param_list_declaration():
  return ZERO_OR_ONE, param, ZERO_OR_MORE, (",", param)
  
def param():
  return re_param

def comment():
  return re_comment

def pseudo():
  return ":", [ function, ident ]

def css3pseudo():
  return ":", pseudo()

def attrib():
  return "[", ident, ZERO_OR_ONE, (attrib_type, [ ident, string ]), "]"

def attrib_type():
  return re_attrib_type
  
def simple_selector():
  return [ (element_name, ZERO_OR_MORE, [hash, class_, attrib, pseudo, css3pseudo]), (ONE_OR_MORE, [hash, class_, attrib, pseudo, css3pseudo]) ]

def combinator():
  return re_combinator

def selector():
  return simple_selector(), ZERO_OR_ONE, (ZERO_OR_ONE, combinator, selector)

def expansion1():
  return propertyname(), "{", declarationblock(), "}"

def expansion2():
  return propertyname(), "(", declarationblock(), ")"

def expansion():
  return [ expansion1(), expansion2() ]

def directive():
  return "@", function(), ";"

def full_selector():
  return selector, ZERO_OR_MORE, (',',  selector )

def plugin():
  return "~", function()

def propertyname():
  return re_name

def propertyvalue():
  return ZERO_OR_MORE, [ math_operation, propertyvalue_pluginextended, plugin, re_css_func, re_property_value_start, re_simple_property ], re_propertyvalue

def pre_plugin_text():
  return rec("[^~;]*")
  
def propertyvalue_pluginextended():
  return re_simple_property, plugin, ZERO_OR_MORE, propertyvalue_pluginextended

def property():
  return property_unterminated(), ";"
  
def property_unterminated():
  return propertyname, ":", propertyvalue

def mediaquery():
  return re.compile("@media\s+[^{]*"), "{", language, "}"

def declarationblock():
  return "{", ZERO_OR_MORE, [ property, directive, comment, declaration, use, expansion, variable_set ], ZERO_OR_ONE, property_unterminated, "}"

def declaration():
  return full_selector(), declarationblock
  
def language():
  return ZERO_OR_MORE, [ builtin_css_directives(), declaration, directive, comment, template, variable_set, mediaquery ]
