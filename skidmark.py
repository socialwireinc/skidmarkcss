# -*- coding: latin-1 -*-

"""The SkidmarkCSS preprocessor"""

import copy
import itertools
import os
import pyPEG
import re
import sys
import time
import StringIO

import skidmarklanguage
from skidmarknodes import SkidmarkHierarchy, n_Declaration, n_Selector, n_DeclarationBlock, n_TextNode, n_Template


#
# Exception Classes
#

class FileNotFound(Exception):
  """Exception used when an input file is not found. this can be the main file
  or an included file"""
  pass

class UnrecognizedParsedTree(Exception):
  """An error occured while parsing the tree. The tree does not have items that
  are recognised"""
  pass

class UnrecognizedSelector(Exception):
  """A selector is not recognised"""
  pass

class Unimplemented(Exception):
  """While parsing the tree we came across something that was not implemented"""
  pass

class ErrorInFile(Exception):
  """There was an error parsin the file"""
  pass

class UnexpectedTreeFormat(Exception):
  """The format of the tree was not what was expected"""
  pass

class UndefinedTemplate(Exception):
  """The requested template could not be loaded"""
  pass

class InvalidTemplateUse(Exception):
  """There is an error in the @@use call"""
  pass

class VariableNotFound(Exception):
  """A requested variable could not be found"""
  pass


#
# Variables and Constants
#

TEMPLATES = {}
VARIABLE_STACK = []

CSS_OUTPUT_COMPRESSED = 0
CSS_OUTPUT_COMPACT = 1
CSS_OUTPUT_CLEAN = 2
CSS_OUTPUT_SINGLELINE = 3
SPACING_CLEAN = 2

OUTPUT_TEMPLATE_DECLARATION = {
  CSS_OUTPUT_SINGLELINE : "%s{%s}",
  CSS_OUTPUT_COMPRESSED : "%s{%s;}",
  CSS_OUTPUT_COMPACT : "%s { %s; }",
  CSS_OUTPUT_CLEAN : "%%s {\n%s%%s;\n}\n" % ( " " * SPACING_CLEAN, )
}

OUTPUT_TEMPLATE_SELECTOR_SEPARATORS = {
  CSS_OUTPUT_SINGLELINE : ",",
  CSS_OUTPUT_COMPRESSED : ",",
  CSS_OUTPUT_COMPACT : ", ",
  CSS_OUTPUT_CLEAN : ",\n"
}

OUTPUT_TEMPLATE_PROPERTY_SEPARATORS = {
  CSS_OUTPUT_SINGLELINE : ";",
  CSS_OUTPUT_COMPRESSED : ";",
  CSS_OUTPUT_COMPACT : "; ",
  CSS_OUTPUT_CLEAN : ";\n%s" % ( " " * SPACING_CLEAN, )
}

OUTPUT_TEMPLATE_PROPERTY_VALUE_SEPARATOR = {
  CSS_OUTPUT_SINGLELINE : ":",
  CSS_OUTPUT_COMPRESSED : ":",
  CSS_OUTPUT_COMPACT : ": ",
  CSS_OUTPUT_CLEAN : ": "
}

OUTPUT_TEMPLATE_COMBINATOR = {
  CSS_OUTPUT_SINGLELINE : "%s",
  CSS_OUTPUT_COMPRESSED : "%s",
  CSS_OUTPUT_COMPACT : " %s",
  CSS_OUTPUT_CLEAN : " %s"
}

OUTPUT_TEMPLATE_DECLARATION_SEPARATOR = {
  CSS_OUTPUT_SINGLELINE : "",
  CSS_OUTPUT_COMPRESSED : "\n",
  CSS_OUTPUT_COMPACT : "\n",
  CSS_OUTPUT_CLEAN : "\n"
}


#
# The Class that makes it all happen!
#

class SkidmarkCSS(object):
  re_variable = re.compile(skidmarklanguage.t_variable)
  re_number = re.compile("^([-+]?(?:\d+(?:\.\d+)?|\d+))")

  def __init__(self, s_infile, s_outfile=None, verbose=True, timer=False, printcss=False, output_format=CSS_OUTPUT_COMPRESSED, show_hierarchy=False, simplify_output=True, parent=None):
    """Create the object by specifying a filename (s_infile) as an argument (string)"""
    
    start_time = time.time()
    
    self.s_infile = s_infile
    self.s_outfile = s_outfile
    self.verbose = verbose
    self.printcss = printcss
    self.output_format = output_format
    self.show_hierarchy = show_hierarchy
    self.simplify_output = simplify_output
    self.timer = timer
    self.src = ""
    self.log_indent_level = 0
    self.math_ops = None
    self.current_template_definition = None
    self.parent = parent
    self.include_base_path = ""
    
    if parent is not None:
      if not isinstance(parent, SkidmarkCSS):
        raise Unimplemented("SkidmarkCSS may only have another SkidmarkCSS as a parent")
      self.log_indent_level = parent.log_indent_level + 1
    
    self.ast = self._parse_file()
    
    self.processed_tree = self._process()
    self._process_output()
    
    if timer and self.log_indent_level == 0:
      self.verbose = True
      self._log("-> Processed '%s' in %.04f seconds" % ( s_infile, time.time() - start_time, ))
      self.verbose = verbose
    
    return
  
  def get_processed_tree(self):
    """Return the object's processed tree"""
    
    return self.processed_tree
  
  def _log(self, s):
    """Print strings to the screen, for debugging"""
    
    leading = self.log_indent_level
    
    s = s.strip()
    if not s:
      return
    
    if self.verbose:
      single_leading_spacer = "    "
      if type(leading) is int and leading:
        if "\n" in s:
          s = "\n".join([ "%s%s" % ( single_leading_spacer * leading, s_cr ) for s_cr in s.split("\n") ])
          print s
        else:
          print "%s%s" % ( single_leading_spacer * leading, s )
      else:
        print s
    return
    
  def _update_log_indent(self, change):
    if self.verbose and type(change) is int:
      self.log_indent_level += change
    return self.log_indent_level
  
  def _parse_file(self):
    """Parses the data using pyPEG, according to the Skidmark Language definition"""
    
    self._log("-" * 72)
    self._log("Loading '%s'" % ( self.s_infile, ))
    self.src = self._get_file_src()
    
    self._update_log_indent(+1)
    self._log("%ld bytes" % ( len(self.src), ))
    self._log("Using pyPEG to obtain the AST")
    self._update_log_indent(-1)
    
    return pyPEG.parseLine(self.src, skidmarklanguage.language, resultSoFar=[], skipWS=True)
  
  def _get_file_src(self):
    """Reads the byte content of self.s_infile and returns it as a string"""
    
    if isinstance(self.s_infile, basestring):
      self._update_log_indent(+1)
      self._log("Reading file contents")
      self._update_log_indent(-1)
      
      src_dir, src_filename = os.path.split(self.s_infile)
      
      if isinstance(self.parent, SkidmarkCSS):
        base_path = self.parent.include_base_path
      else:
        self.include_base_path = src_dir
        base_path = src_dir
      
      self.s_infile = os.path.join(os.path.join(*os.path.split(base_path)), os.path.join(*os.path.split(self.s_infile)))
      
      try:
        src = open(self.s_infile, "rb").read()
      except IOError:
        raise FileNotFound(self.s_infile)
      return src

    if hasattr(self.s_infile, 'read') and callable(self.s_infile.read):
      return self.s_infile.read()

    raise TypeError("s_infile must be a filename (string) or file-like object.")

  def _process(self):
    """Processes the AST that has been generated in __init__"""
    
    tree, remainder = self.ast
    if remainder.strip():
      error_line = 1 + self.src.rstrip().count("\n") - remainder.count("\n")
      raise ErrorInFile("Error parsing '%s'\nLine %d: %s" % ( self.s_infile, error_line, remainder.strip().split("\n")[0] ))
    
    tree_len = len(tree)
    if tree_len != 1:
      raise UnrecognizedParsedTree("Root element should have a single element, not %d" % ( tree_len, ))
    
    self._log("Walking through the AST to create an object tree")
    data = self._process_node(tree[0])
    self._log("Walking through AST has completed")
    
    # We may not get anything valuable back (an include file may simply have variable
    # definitions... no tree in that case).  Clean this up if this is the case.
    data = [ item for item in data if item ]
    return data
  
  def _process_output(self):    
    data = self.get_processed_tree()
    
    if self.show_hierarchy:
      verbose_mode = self.verbose
      self.verbose = True
      
      self._log("Generated the following hierarchy")
      description = []
      for node in data:
        if isinstance(node, SkidmarkHierarchy):
          description = node.describe_hierarchy(self.log_indent_level, description)
      
      self._update_log_indent(+1)
      self._log("\n".join(description))
      self._update_log_indent(-1)
      
      self.verbose = verbose_mode
    
    css = self._generate_css(data)
    css_str = OUTPUT_TEMPLATE_DECLARATION_SEPARATOR[self.output_format].join(css)
    
    if self.verbose and not self.printcss:
      self._log("Generated CSS")
      self._update_log_indent(+1)
      self._log(css_str)
      self._update_log_indent(-1)
      
    self._create_outfile(css_str)
    
    self._log("=" * 72)
    self._log("Completed processing %s, generated %d bytes" % ( self.s_infile, len(css_str) ))
    
    return
    
  def _generate_css(self, tree=None):
    """Builds the output CSS
    Returns a list (each line of the CSS output)"""
    
    if tree is None:
      tree = self.get_processed_tree()
    
    # The outer level of the tree should be a list
    if type(tree) is not list:
      raise UnexpectedTreeFormat("The tree format passed to the _generate_css() method is not recognized")
    
    css = []
    for node in tree:
      if isinstance(node, n_TextNode):
        css.append(node.text)
        continue
      
      if type(node) is list:
        blocks = []
        for _node in node:
          blocks.extend(self._generate_css_get_blk_selectors(_node))
      else:
        blocks = self._generate_css_get_blk_selectors(node)
      
      for all_selectors, blk in blocks:
        if self.simplify_output:
          blk.simplify_shorthandables()
        
        css.append(OUTPUT_TEMPLATE_DECLARATION[self.output_format] % (
          OUTPUT_TEMPLATE_SELECTOR_SEPARATORS[self.output_format].join(all_selectors),
          OUTPUT_TEMPLATE_PROPERTY_SEPARATORS[self.output_format].join(blk.properties)
        ))
    
    return css
  
  def _generate_css_get_blk_selectors(self, node):
    declaration_blocks = []
    if isinstance(node, SkidmarkHierarchy):
      declaration_blocks = node.find_child_declaration_blocks(declaration_blocks)
    
    blocks = []
    for blk in declaration_blocks:
      declarations = []
      declarations = blk.find_parent_declarations(declarations)
      declarations.reverse()
      
      selectors = []
      for dec in declarations:
        selectors.append([ selector.selector for selector in dec.selectors])
        
      all_selectors = [ " ".join(s) for s in self._simplyfy_selectors(itertools.product(*selectors)) ]
      blocks.append(( all_selectors, blk ))
    
    return blocks
  
  def _simplyfy_selectors(self, selectors):
    """Runs to the list of selectors and simplifies anything can can be simplified.
    The simplest example is to transfer the "&" selectors to its parent."""
    
    if not selectors:
      return selectors
    
    groups = []
    
    selectors = list(selectors)
    for selector_group in selectors:
      selector_list = [ selector_group[0] ]
      for selector in selector_group[1:]:
        if selector.startswith("&"):
          selector_list[-1] = "%s%s" % ( selector_list[-1], selector[1:] )
        else:
          selector_list.append(selector)
      
      groups.append(selector_list)
    
    return groups
    
  def _create_outfile(self, css_text):
    """Generates the output file (self.s_outfile)"""
    
    if self.s_outfile or self.printcss:
      self._log("Generating %s" % ( self.s_outfile or "CSS to stdout", ))
    
    if self.s_outfile:
      if isinstance(self.s_outfile, StringIO.StringIO):
        self.s_outfile.write(css_text + "\n")
      else:
        open(self.s_outfile, "wt").write(css_text + "\n")
    
    if self.printcss:
      sys.stdout.write(css_text + "\n")
    
    return
  
  def _process_node(self, node, parent=None):
    """Process a single node from the AST"""
    
    node_len = len(node)
    if node_len != 2:
      raise UnrecognizedParsedTree("Nodes should only have 2 elements, not %d: %s" % ( node_len, str(node) ))
    
    self._update_log_indent(+1)
    fn_name = "".join([ "_nodeprocessor_", node[0] ])
    self._log("@%s -> P = %s" % ( fn_name, parent ))
    
    if not hasattr(self, fn_name) or not hasattr(getattr(self, fn_name), "__call__"):
      raise Unimplemented("Node type is unimplemented: %s" % ( fn_name, ))
    
    processor_result = getattr(self, fn_name)(node[1], parent)
    self._log(">>> Processor Result (@%s) >>> %s" % ( fn_name, processor_result or 'an empty result, discarding', ))
    
    if type(processor_result) is list:
      for pr in processor_result:
        if isinstance(parent, SkidmarkHierarchy) and isinstance(pr, SkidmarkHierarchy):
          parent.add_child(pr)
    else:
      if isinstance(parent, SkidmarkHierarchy) and isinstance(processor_result, SkidmarkHierarchy):
        parent.add_child(processor_result)
    
    self._update_log_indent(-1)
    return processor_result
  
  def get_variable_value(self, variable):
    """Runs through the variable stack lloking for the requested variable.
    Returns the property value."""
    
    variable = variable.strip()
    
    if self.current_template_definition:
      return variable
    
    if variable.startswith("$"):
      variable = variable[1:]
    
    stack = copy.deepcopy(VARIABLE_STACK)
    
    while stack:
      variable_set = stack.pop()
      if variable in variable_set:
        return variable_set[variable]
    
    raise VariableNotFound("Variable '$%s' is undefined" % ( variable, ))
  
  @classmethod
  def get_variables_from_text(cls, text):
    variables = set()
    
    mo = SkidmarkCSS.re_variable.search(text)
    while mo:
      variables.add(text[mo.start():mo.end()])
      text = text[mo.end():]
      mo = SkidmarkCSS.re_variable.search(text)
    
    return list(variables)
  
  def update_property(self, property):
    """Verifies the property to see if the value is a reference to a variable.
    Returns an updated property (or an unmodified property if it was not required."""
    
    prop_name, prop_value = n_DeclarationBlock.get_property_parts(property)
    
    all_variables = SkidmarkCSS.get_variables_from_text(prop_value)
    for variable in all_variables:
      property = property.replace(variable, self.get_variable_value(variable))
    
    return property
  
  def get_math_ops(self):
    """Returns the MathOperations class for this object. If it has not yet
    been defined it will be created before it is returned"""
    
    if self.math_ops is None:
      self.math_ops = MathOperations(self)
    
    return self.math_ops
  
  @classmethod
  def get_number_parts(cls, number):
    """Retrieve the number and measurement.
    Example: "12px" -> ( "12", "px" )"""
    
    num_cast = { True: float, False: int }
    
    mo = SkidmarkCSS.re_number.match(number)
    if mo and mo.group():
      value = num_cast["." in mo.group()](mo.group())
    else:
      value = 0
    
    s = number.split(str(value))
    if len(s) == 2:
      return value, s[1].strip()
    return value, ""

  
  #
  # Node Processors: What runs through the AST
  #
  
  def _nodeprocessor_language(self, data, parent):
    """Node Processor: language"""
    
    declarations = []
    for node_data in data:
      node = self._process_node(node_data)
      
      # If the node is an empty string, it is because we processed a comment in the source.
      # Ignore it.  Only process those that don't fit this criteria.
      if not (isinstance(node, basestring) and not node):
        declarations.append(node)
    
    return declarations
  
  def _nodeprocessor_declaration(self, data, parent):
    """Node Processor: declaration"""
    
    oDeclaration = n_Declaration(parent)
    
    parts = []
    for node_data in data:
      part = self._process_node(node_data, oDeclaration)
      parts.append(part)
    
    selectors, declarationblock = (parts[:-1], parts[-1])
    oDeclaration.add_selectors(selectors)
    oDeclaration.set_declarationblock(declarationblock)
    
    return oDeclaration
  
  def _nodeprocessor_selector(self, data, parent):
    """Node Processor: selector"""
    
    selector_parts = self._nodepprocessor_helper_selector(data)
    return n_Selector(parent, " ".join(selector_parts))
    
  def _nodepprocessor_helper_selector(self, data):
    """Node Processor Helper Function: selector"""
    
    selector_parts = []
    attribute = ""
    
    while data:
      current_element = data.pop(0)
      selector_type, selector_item = current_element
      
      if selector_type == "element_name":
        selector_parts.append(selector_item)
      elif selector_type in ("pseudo", "css3pseudo"):
        if selector_type == "css3pseudo":
          pseudo_str = "::"
        else:
          pseudo_str = ":"
        
        for pseudo_type, pseudo_item in selector_item:
          if pseudo_type == "ident":
            if selector_parts:
              selector_parts[-1] = "%s%s%s" % ( selector_parts[-1], pseudo_str, pseudo_item )
            else:
              selector_parts.append(pseudo_str + pseudo_item)
          elif pseudo_type == "function":
            raise Unimplemented("%s has not yet been implemented" % ( str(selector_item), ))
      elif selector_type == "class_":
        if selector_parts:
          selector_parts[-1] = "%s%s" % ( selector_parts[-1], selector_item )
        else:
          selector_parts.append(selector_item)
      elif selector_type == "hash":
        if selector_parts:
          selector_parts[-1] = "%s%s" % ( selector_parts[-1], selector_item )
        else:
          selector_parts.append(selector_item)
      elif selector_type == "combinator":
        combinator_symbol = OUTPUT_TEMPLATE_COMBINATOR[self.output_format] % ( "".join(selector_item).strip(), )
        selector_parts[-1] = "%s%s" % ( selector_parts[-1], combinator_symbol )
      elif  selector_type == "selector":
        selector_parts.extend(self._nodepprocessor_helper_selector(selector_item))
      elif selector_type == "attrib":
        if len(selector_item) not in (1, 3) or selector_item[0][0] != "ident":
          raise UnrecognizedSelector("Unrecognized value for an attrib: %s" % ( str(selector_item), ))
        
        attribute = selector_item[0][1]
        for attrib_item in selector_item[1:]:
          if attrib_item[0] in ("attrib_type", "ident", "string"):
            attribute += attrib_item[1]
          else:
            raise UnrecognizedSelector("Unrecognized value for an attrib: %s" % ( str(selector_item), ))
      else:
        raise UnrecognizedSelector(selector_type + ":" + str(selector_item))
      
    # Join the attributes to the selector
    if attribute:
      parts = [ "%s[%s]" % ( sp, attribute ) for sp in selector_parts ]
    else:
      parts = selector_parts
    
    return parts
  
  def _nodeprocessor_declarationblock(self, data, parent):
    """Node Processor: declarationblock"""
    
    self._log("V Creating a new variable set in the stack")
    VARIABLE_STACK.append({})
    
    oDeclarationBlock = n_DeclarationBlock(parent, self.simplify_output)
    
    for node_data in data:
      property = self._process_node(node_data, oDeclarationBlock)
      if property and isinstance(property, basestring):
        if isinstance(parent, n_Declaration):
          property = self.update_property(property)
        
        oDeclarationBlock.add_property(property)
    
    VARIABLE_STACK.pop()
    self._log("V Removing last variable set, remaining stack: %s" % ( str(VARIABLE_STACK), ))
    
    return oDeclarationBlock
    
  def _nodeprocessor_property(self, data, parent):
    """Node Processor: property"""
    
    name, value = ("", "")
    for property_type, property_item in data:
      if property_type == "propertyname":
        name = property_item.strip()
      elif property_type == "propertyvalue":
        if isinstance(property_item, basestring):
          value = property_item.strip()
        elif type(property_item) is list:
          value = self._process_node(property_item[0], parent=None)
        else:
          raise Unimplemented("Unrecognized value for parameter '%s', got '%s'" % ( name or '?', str(property_item) ))
      else:
        raise Unimplemented("Unknown property type '%s'" % ( property_type, ))
        
    if not name or not value:
      raise UnrecognizedParsedTree("Failure during property parsing: %s" % ( str(data), ))
    return "%s%s%s" % ( name, OUTPUT_TEMPLATE_PROPERTY_VALUE_SEPARATOR[self.output_format], value )
  
  def _nodeprocessor_property_unterminated(self, data, parent):
    """Node Processor: property_unterminated"""
    
    return self._nodeprocessor_property(data, parent)
  
  def _nodeprocessor_directive(self, data, parent):
    """Node Processor: directive"""
    
    function_name, param_list = ( data[0], [ self._process_node(node) for node in data[1:] ] )
    fn_name = "".join([ "_directive_", function_name ])
    
    self._update_log_indent(+1)
    self._log("@%s -> P = %s" % ( fn_name, parent ))
    
    if not hasattr(self, fn_name) or not hasattr(getattr(self, fn_name), "__call__"):
      raise Unimplemented("Directive is unimplemented: %s" % ( fn_name, ))
      
    directive_result = getattr(self, fn_name)(parent, *param_list)
    
    self._log(">>> Directive Result (@%s) >>> %s" % ( fn_name, directive_result or 'nothing, discarding', ))
    
    self._update_log_indent(-1)
    return directive_result
  
  def _nodeprocessor_string(self, data, parent):
    return data
  
  def _nodeprocessor_param(self, data, parent):
    if isinstance(data, basestring):
      return data
    
    raise Unimplemented("param argument unknown: %s" % ( str(data), ))
  
  def _nodeprocessor_comment(self, data, parent):
    """Node Processor: comment"""
    
    return ""
    
  def _nodeprocessor_import_rule(self, data, parent):
    """Processor for the '@import url();' rule"""
    
    return n_TextNode(parent, data)
    
  def _nodeprocessor_charset_rule(self, data, parent):
    """Processor for the '@charset' rule"""
    
    return n_TextNode(parent, data)
  
  def _nodeprocessor_template(self, data, parent):
    """Define a template that may be reused several times throughout this CSS"""
    
    template_name = data[0]
    parameters = data[1:-1]
    declaration_node = data[-1]
    
    # Keep track of the template definition we are on
    if not self.current_template_definition:
      self.current_template_definition = template_name
    
    params = [ parameter[1] or "" for parameter in parameters ]    
    if len(params) == 1 and not params[0]:
      params = []
    
    dec_block = self._process_node(declaration_node, parent=None)
    
    TEMPLATES[template_name] = n_Template(None, template_name, params, dec_block)
    
    # If we are the top-level template, then keep track that we're done!
    if self.current_template_definition == template_name:
      self.current_template_definition = None
    
    return ""
  
  def _nodeprocessor_use(self, data, parent):
    """Indicate that we with to use a template.
    The template must exist before @@use may be called"""
    
    template_name = data[0]
    parameters = data[1:]
    
    params_raw = [ self._process_node(parameter) or "" for parameter in parameters ]
    params = []
    for param in params_raw:
      if isinstance(param, basestring) and param[0] in ("'", '"') and param[0] == param[-1] and len(param) > 1:
        params.append(param[1:-1])
      else:
        params.append(param)
    
    if len(params) == 1 and not params[0]:
      params = []
    
    template = TEMPLATES.get(template_name)
    
    # Verify that this template has been defined
    if not template:
      raise UndefinedTemplate("Template '%s' has not been defined" % ( template_name, ))
      
    # Verify the parameters
    if not template.params_are_valid(params):
      # It would be ideal if we could identify the line number, but I don't think it's possible with a properly parsed pypeg file
      raise InvalidTemplateUse("The '%s' template expects %d parameter%s, not %d" % ( template_name, len(template.params), len(template.params) != 1 and "s" or "", len(params) ))
    
    # Clone the declaration block so that we do not alter the template
    dec_block = template.declarationblock.clone(parent)
    
    # Transfer the children to the proper parent
    for child in dec_block.iter_children():
      parent.add_child(child)
    
    # Everything is good, replace all the params
    param_substitutions = zip(template.params, params)
    
    properties = []
    for property in dec_block.properties:
      for search, replace in param_substitutions:
        property = property.replace(search, replace)
      properties.append(self.update_property(property))
    
    # TODO: We need to iterate through the children's properties as well... we don't know how
    #       many levels the tree has, it needs to recurse through them all...
    
    # Add the properties to the parent
    if isinstance(parent, n_DeclarationBlock) and hasattr(parent, "properties"):
      for property in properties:
        parent.add_property(property)
        
    return ""
  
  def _nodeprocessor_expansion(self, data, parent):
    root_name = data[0]
    elements = data[1:]
    
    self._update_log_indent(+1)
    self._log("Preparing for the expansion of '%s'" % ( root_name, ))
    
    properties = []
    for node_data in elements:
      node_result = self._process_node(node_data, None)
      
      if type(node_result) is not list:
        node_result = [ node_result ]
      
      for result in node_result:
        property = "%s-%s" % ( root_name, result )
        properties.append(property)
      
    self._update_log_indent(-1)
    
    if isinstance(parent, n_DeclarationBlock) and properties:
      for property in properties:
        property = self.update_property(property)
        parent.add_property(property)
    
    return properties
  
  def _nodeprocessor_variable_set(self, data, parent):
    """Process a variable assignment"""
    
    param_name = data[0][1:] # ignore the leading '$'
    elements = data[1:]
    
    for node_data in elements:
      param_value = self._process_node(node_data, None)
      for quote_char in ('"', "'"):
        if param_value.startswith(quote_char) and param_value.endswith(quote_char):
          param_value = param_value.strip(quote_char)
      
      if len(VARIABLE_STACK) == 0:
        # We have not created anything yet, create the first slot (globals)
        self._log("V Created the globals space and added '%s' = '%s'" % ( param_name, param_value ))
        VARIABLE_STACK.append({param_name: param_value})
      else:
        # A stack already exists, add the variable to the latest stack
        VARIABLE_STACK[-1][param_name] = param_value
        self._log("V Added '%s' = '%s' to stack #%d" % ( param_name, param_value, len(VARIABLE_STACK) ))
      
      self._log("V Current Stack: %s" % ( str(VARIABLE_STACK), ))
    
    return ""
    
  def _nodeprocessor_variable(self, data, parent):
    """Return the value of this variable"""
    
    return self.get_variable_value(data)
  
  def _nodeprocessor_constant(self, data, parent):
    """A constant -- not much to process here"""
    
    if isinstance(data, basestring):
      if data.startswith("$"):
        # Return the value. An exception will be raised if the variable doesn't exist!
        return self.get_variable_value(data)
      constant = data
    else:
      raise Unimplemented("expression '%s' in unimplemented" % ( str(data), ))
    
    return constant
  
  def _nodeprocessor_math_operation(self, data, parent):
    """A math expression parser -- does its best!"""

    sequence = self._nodeprocessor_math_operation_helper(data)
    return self.get_math_ops().reduce_group(sequence)
  
  def _nodeprocessor_math_group(self, data, parent):
    """Processes a math group (math expressions found within parentheses)"""
    
    return self._nodeprocessor_math_operation_helper(data)
  
  def _nodeprocessor_math_operation_helper(self, data):
    """Helper Function: Returns a normalized sequence of operations (Python list)"""
    
    seq = []
    for item in data:
      if isinstance(item, basestring):
        seq.append(item)
      else:
        seq.append(self._process_node(item))
        
    return seq
  
  
  #
  # Directives
  #
  
  def _directive_include(self, parent, filename):
    """Include a seperate file, inline, as if all the lines were local
    Returns the processed tree (list) of the parsed AST"""
    
    if isinstance(filename, basestring):
      if filename.startswith('"') and filename.endswith('"'):
        filename = filename[1:-1]
      elif filename.startswith("'") and filename.endswith("'"):
        filename = filename[1:-1]
        
      # Include the file by instantiating a new object to process it
      sm = SkidmarkCSS(filename,
                       s_outfile=None,
                       output_format=self.output_format,
                       timer=self.timer,
                       show_hierarchy=self.show_hierarchy,
                       verbose=self.verbose,
                       simplify_output=self.simplify_output,
                       parent=self)
      
      tree = sm.get_processed_tree()
      if tree:
        for branch in tree:
          branch.parent = parent
          if parent:
            parent.add_child(branch)
        return tree
    return []


class MathOperations(object):
  """Defines the math operators"""
  
  # Define ops, division defined in __init__
  ops = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
  }

  def __init__(self, parent):
    """Initialize the object, setting the SkidmarkCSS object as a parent"""
    
    if not isinstance(parent, SkidmarkCSS):
      raise Unimplemented("The parent passed to the MathOperations object must be a SkidmarkCSS object")
    
    smObject = parent
    
    # Define the division operator (ignore floating point if it has no significance)
    def division(a, b):
      r = (a * 1.0) / b
      if divmod(r, int(r))[1] == 0:
        return int(r)
      return r
    
    MathOperations.ops["/"] = division
  
  @classmethod
  def reduce_group(cls, data):
    """Reduces the groups by computing the elements it is able to handle at the
    current moment. Recurses in order to process all it can.
    Returns the computed value from the data provided."""
    
    seq = []
    for item in data:
      if type(item) is list:
        seq.append(cls.reduce_group(item))
      else:
        seq.append(item)
    return cls.compute(seq)
  
  @classmethod
  def compute(cls, seq):
    """Processes the sequence, applying the math operations.
    Returns a final computed data (string), including the measurement from
    the data (if applicable)"""
    
    loop_start = 1
    if "*" in seq or "/" in seq:
      loop_start = 2
  
    # Initialize the new sequence (for once we've processed * and /)
    n_seq = []
    
    for loop in map(lambda x: x - 1, range(loop_start, 0, -1)):
      # loop=1 = process *, /
      # loop=0 = process +, -
      
      L = seq.pop(0)
      while seq:
        op = seq.pop(0)
        R = seq.pop(0)
        
        Li, Lmeasure = SkidmarkCSS.get_number_parts(L)
        Ri, Rmeasure = SkidmarkCSS.get_number_parts(R)

        if not (Lmeasure == Rmeasure or not Lmeasure or not Rmeasure):
          raise Unimplemented("It is not possible to compute '%s %s %s'" % ( Lmeasure.strip(), op.strip(), Rmeasure.strip() ))
        
        if not op in cls.ops:
          raise Unimplemented("Math expression %s is not implemented" % ( op, ))
        
        if loop == 1:
          if op in ("*", "/"):
            L = str(cls.ops.get(op)(Li, Ri)) + (Lmeasure or Rmeasure)
            if not seq:
              n_seq.append(L)
          else:
            n_seq.extend([L, op])
            if not seq:
              n_seq.append(R)
            else:
              L = R
        else:
          L = str(cls.ops.get(op)(Li, Ri)) + (Lmeasure or Rmeasure)
        
      if loop == 1:
        seq = n_seq
    
    return L


# ----------------------------------------------------------------------------

def simple_process_file(infile):
  try:
    sm = SkidmarkCSS(infile, verbose=False, output_format=CSS_OUTPUT_CLEAN)
    print "\n".join(sm._generate_css())
  except:
    err = """body:before { content: \""""
    try:
      raise
    except Unimplemented, e:
      err += "%s: %s" % ( e.__class__.__name__, str(e).strip().replace("\n", " -- ") )
    except UnrecognizedParsedTree, e:
      err += "%s: %s" % ( e.__class__.__name__, str(e).strip().replace("\n", " -- ") )
    except UnexpectedTreeFormat, e:
      err += "%s: %s" % ( e.__class__.__name__, str(e).strip().replace("\n", " -- ") )
    except ErrorInFile, e:
      err += "%s: %s" % ( e.__class__.__name__, str(e).strip().replace("\n", " -- ") )
    except UnrecognizedSelector, e:
      err += "%s: %s" % ( e.__class__.__name__, str(e).strip().replace("\n", " -- ") )
    except FileNotFound, e:
      err += "%s: %s" % ( e.__class__.__name__, str(e).strip().replace("\n", " -- ") )
    except UndefinedTemplate, e:
      err += "%s: %s" % ( e.__class__.__name__, str(e).strip().replace("\n", " -- ") )
    except InvalidTemplateUse, e:
      err += "%s: %s" % ( e.__class__.__name__, str(e).strip().replace("\n", " -- ") )
    except VariableNotFound, e:
      err += "%s: %s" % ( e.__class__.__name__, str(e).strip().replace("\n", " -- ") )
    except Exception, e:
      err += "%s: %s" % ( e.__class__.__name__, str(e).strip().replace("\n", " -- ") )
    finally:
      err += """\"; }"""
   
    print err

def processFromString(src_str, **kw):
  """Parse the SkidmarkCSS supplied as a string and returns the CSS as a string"""
  
  infile = StringIO.StringIO(src_str)
  outfile = StringIO.StringIO()
  params = dict([ (k, v) for k, v in kw.iteritems() if k not in ["infile", "outfile"] ])
  params['return_err'] = True
  err = execute_sm(infile=infile, outfile=outfile, **params)
  
  return ( outfile.getvalue(), err )

def execute_sm(**kw):
  infile = kw.get('infile')
  outfile = kw.get('outfile')
  verbose = kw.get('verbose')
  timer = kw.get('timer', False)
  printcss = kw.get('printcss', False)
  output_format = kw.get('output_format', CSS_OUTPUT_COMPRESSED)
  show_hierarchy = kw.get('show_hierarchy', False)
  simplify_output = kw.get('simplify_output', True)
  
  err = []
  
  try:
    sm = SkidmarkCSS(infile,
                     s_outfile=outfile,
                     verbose=verbose,
                     timer=timer,
                     printcss=printcss,
                     output_format=output_format,
                     show_hierarchy=show_hierarchy,
                     simplify_output=simplify_output)
  except:
    err.append("-=" * (72/2))
    try:
      raise
    except Unimplemented, e:
      err.append("%s: %s" % ( e.__class__.__name__, str(e) ))
    except UnrecognizedParsedTree, e:
      err.append("%s: %s" % ( e.__class__.__name__, str(e) ))
    except UnexpectedTreeFormat, e:
      err.append("%s: %s" % ( e.__class__.__name__, str(e) ))
    except ErrorInFile, e:
      err.append("%s: %s" % ( e.__class__.__name__, str(e) ))
    except UnrecognizedSelector, e:
      err.append("%s: %s" % ( e.__class__.__name__, str(e) ))
    except FileNotFound, e:
      err.append("%s: %s" % ( e.__class__.__name__, str(e) ))
    except UndefinedTemplate, e:
      err.append("%s: %s" % ( e.__class__.__name__, str(e) ))
    except InvalidTemplateUse, e:
      err.append("%s: %s" % ( e.__class__.__name__, str(e) ))
    except VariableNotFound, e:
      err.append("%s: %s" % ( e.__class__.__name__, str(e) ))
    except Exception, e:
      raise
    finally:
      err.append("-=" * (72/2))
  
  err = "\n".join(err)
  if kw.get("return_err"):
    return err
  
  print err
  
  return

def get_arguments():
  import argparse
  
  arg_parser = argparse.ArgumentParser(
    description="Leave your mark on the web using SkidmarkCSS",
    epilog="Leaving a trace since 2011",
    add_help=True
  )
  
  arg_parser.add_argument("-i", dest="infile", help="The input file", nargs=1, metavar="srcfile")
  arg_parser.add_argument("-o", dest="outfile", help="The output file", nargs=1, metavar="dstfile")
  arg_parser.add_argument("-v", "--verbose", dest="verbose", help="Display detailed information", action="store_true")
  arg_parser.add_argument("-p", "--printcss", dest="printcss", help="Output the final CSS to stdout", action="store_true")
  arg_parser.add_argument("-t", "--timer", dest="timer", help="Display timer information", action="store_true")
  arg_parser.add_argument("--hierarchy", dest="hierarchy", help="Display the object hierarchy representing the CSS", action="store_true")
  arg_parser.add_argument("--clean", dest="format", help="Outputs the CSS in 'clean' format", action="store_const", const=CSS_OUTPUT_CLEAN)
  arg_parser.add_argument("--compact", dest="format", help="Outputs the CSS in 'compact' format (default)", action="store_const", const=CSS_OUTPUT_COMPACT)
  arg_parser.add_argument("--compressed", dest="format", help="Outputs the CSS in 'compressed' format", action="store_const", const=CSS_OUTPUT_COMPRESSED)
  arg_parser.add_argument("--singleline", dest="format", help="Outputs the CSS in 'single line' format (ultra compressed)", action="store_const", const=CSS_OUTPUT_SINGLELINE)
  arg_parser.add_argument("-ns", "--nosimplify", dest="simplify_output", help="Do not simplify the output by using shorthand notions where possible", action="store_false")
  
  return arg_parser.parse_args()

if __name__ == '__main__':
  args = get_arguments()
  
  infile = args.infile and args.infile[0] or None
  outfile = args.outfile and args.outfile[0] or None
  
  if args.format in (CSS_OUTPUT_COMPRESSED, CSS_OUTPUT_COMPACT, CSS_OUTPUT_CLEAN, CSS_OUTPUT_SINGLELINE):
    output_format = args.format
  else:
    output_format = CSS_OUTPUT_COMPACT
  
  if not args.printcss and not outfile:
    args.printcss = True

  if not infile:
    raise Exception("An input file is required, use -h for help")
    
  execute_sm(infile=infile,
             outfile=outfile,
             verbose=args.verbose,
             timer=args.timer,
             printcss=args.printcss,
             output_format=output_format,
             show_hierarchy=args.hierarchy,
             simplify_output=args.simplify_output)
