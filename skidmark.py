# -*- coding: latin-1 -*-

import copy
import itertools
import pyPEG
import re
import sys
import time

import skidmarklanguage
from skidmarknodes import *

class FileNotFound(Exception): pass
class UnrecognizedParsedTree(Exception): pass
class UnrecognizedSelector(Exception): pass
class Unimplemented(Exception): pass
class ErrorInFile(Exception): pass
class UnexpectedTreeFormat(Exception): pass
class UndefinedTemplate(Exception): pass
class InvalidTemplateUse(Exception): pass
class VariableNotFound(Exception): pass

TEMPLATES = {}
VARIABLE_STACK = []

CSS_OUTPUT_COMPRESSED = 0
CSS_OUTPUT_COMPACT = 1
CSS_OUTPUT_CLEAN = 2
SPACING_CLEAN = 2

OUTPUT_TEMPLATE_DECLARATION = {
  CSS_OUTPUT_COMPRESSED : "%s{%s;}",
  CSS_OUTPUT_COMPACT : "%s { %s; }",
  CSS_OUTPUT_CLEAN : "%%s {\n%s%%s;\n}\n" % ( " " * SPACING_CLEAN, )
}

OUTPUT_TEMPLATE_SELECTOR_SEPARATORS = {
  CSS_OUTPUT_COMPRESSED : ",",
  CSS_OUTPUT_COMPACT : ", ",
  CSS_OUTPUT_CLEAN : ",\n"
}

OUTPUT_TEMPLATE_PROPERTY_SEPARATORS = {
  CSS_OUTPUT_COMPRESSED : ";",
  CSS_OUTPUT_COMPACT : "; ",
  CSS_OUTPUT_CLEAN : ";\n%s" % ( " " * SPACING_CLEAN, )
}

OUTPUT_TEMPLATE_PROPERTY_VALUE_SEPARATOR = {
  CSS_OUTPUT_COMPRESSED : ":",
  CSS_OUTPUT_COMPACT : ": ",
  CSS_OUTPUT_CLEAN : ": "
}

class SkidmarkCSS(object):
  def __init__(self, s_infile, s_outfile=None, verbose=True, timer=False, printcss=False, output_format=CSS_OUTPUT_COMPRESSED, show_hierarchy=False, verbose_indent_level=0):
    """Create the object by specifying a filename (s_infile) as an argument (string)"""
    
    start_time = time.time()
    
    self.s_infile = s_infile
    self.s_outfile = s_outfile
    self.verbose = verbose
    self.printcss = printcss
    self.output_format = output_format
    self.show_hierarchy = show_hierarchy
    self.timer = timer
    self.log_id = verbose_indent_level
    self.src = ""
    self.ast = self._parse_file()
    self.processed_tree = self._process()
    self._process_output()
    
    if timer and self.log_id == 0:
      self.verbose = True
      self._log("-> Processed '%s' in %.04f seconds" % ( s_infile, time.time() - start_time, ))
      self.verbose = verbose
    
    return
  
  def get_processed_tree(self):
    """Return the object's processed tree"""
    
    return self.processed_tree
  
  def _log(self, s):
    """Print strings to the screen, for debugging"""
    
    leading = self.log_id
    
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
      self.log_id += change
    return self.log_id
  
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
    
    self._update_log_indent(+1)
    self._log("Reading file contents")
    self._update_log_indent(-1)
    
    try:
      src = open(self.s_infile, "rb").read()
    except IOError:
      raise FileNotFound(self.s_infile)
    return src

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
    
    return data
  
  def _process_output(self):    
    data = self.get_processed_tree()
    
    if self.show_hierarchy:
      verbose_mode = self.verbose
      self.verbose = True
      
      self._log("Generated the following hierarchy")
      description = []
      for node in data:
        description = node.describe_hierarchy(self.log_id, description)
      
      self._update_log_indent(+1)
      self._log("\n".join(description))
      self._update_log_indent(-1)
      
      self.verbose = verbose_mode
    
    css = self._generate_css(data)
    if self.verbose and not self.printcss:
      self._log("Generated CSS")
      
      self._update_log_indent(+1)
      for css_line in css:
        self._log(css_line)
      self._update_log_indent(-1)
      
    self._create_outfile("\n".join(css))
      
    self._log("=" * 72)
    self._log("Completed processing %s" % ( self.s_infile, ))
    
    return data
    
  def _generate_css(self, tree):
    """Builds the output CSS
    Returns a list (each line of the CSS output)"""
    
    # The outer level of the tree should be a list
    if not type(tree) is list:
      raise UnexpectedTreeFormat("The tree format passed to the _generate_css() method is nor recognized")
    
    css = []
    for node in tree:
      if isinstance(node, n_TextNode):
        css.append(node.text)
        continue
      
      declaration_blocks = []
      if isinstance(node, SkidmarkHierarchy):
        declaration_blocks = node.find_child_declaration_blocks(declaration_blocks)
        
      for blk in declaration_blocks:
        declarations = []
        declarations = blk.find_parent_declarations(declarations)
        declarations.reverse()
        
        selectors = []
        for dec in declarations:
          selectors.append([ selector.selector for selector in dec.selectors])
          
        all_selectors = [ " ".join(s) for s in self._simplyfy_selectors(itertools.product(*selectors)) ]
        
        css.append(OUTPUT_TEMPLATE_DECLARATION[self.output_format] % (
          OUTPUT_TEMPLATE_SELECTOR_SEPARATORS[self.output_format].join(all_selectors),
          OUTPUT_TEMPLATE_PROPERTY_SEPARATORS[self.output_format].join(blk.properties)
        ))
    
    return css
  
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
      open(self.s_outfile, "wt").write(css_text + "\n")
    
    if self.printcss:
      sys.stdout.write(css_text + "\n")
    
    return
  
  def _process_node(self, node, parent=None):
    """Process a single node from the AST"""
    
    node_len = len(node)
    if node_len != 2:
      raise UnrecognizedParsedTree("Nodes should only have 2 elements, not %d: %s" % ( node_len, str(node) ))
    
    self.log_id += 1
    fn_name = "".join([ "_nodeprocessor_", node[0] ])
    self._log("@%s" % ( fn_name, ))
    self._log("P = %s" % ( parent, ))
    
    if not hasattr(self, fn_name) or not hasattr(getattr(self, fn_name), "__call__"):
      raise Unimplemented("Node type is unimplemented: %s" % ( fn_name, ))
    
    processor_result = getattr(self, fn_name)(node[1], parent)
    self._update_log_indent(+1)
    self._log(">>> Result > %s" % ( processor_result or 'an empty result, discarding', ))
    self._update_log_indent(-1)
    
    if type(processor_result) is list:
      for pr in processor_result:
        if isinstance(parent, SkidmarkHierarchy) and isinstance(pr, SkidmarkHierarchy):
          parent.add_child(pr)
    else:
      if isinstance(parent, SkidmarkHierarchy) and isinstance(processor_result, SkidmarkHierarchy):
        parent.add_child(processor_result)
    
    self.log_id -= 1
    return processor_result
  
  def get_variable_value(self, variable):
    """Runs through the variable stack lloking for the requested variable.
    Returns the property value."""
    
    stack = copy.deepcopy(VARIABLE_STACK)
    
    while stack:
      variable_set = stack.pop()
      if variable in variable_set:
        return variable_set[variable]
    
    raise VariableNotFound("Variable '$%s' is undefined" % ( variable, ))
    
  def update_property(self, property):
    """Verifies the property to see if the value is a reference to a variable.
    Returns an updated property (or an unmodified property if it was not required."""
    
    prop_name, prop_value = n_DeclarationBlock.get_property_parts(property)
    
    if prop_value.startswith("$"):
      property = property.replace(prop_value, self.get_variable_value(prop_value[1:]))
    
    return property
  
  
  #
  # Node Processors: What runs through the AST
  #
  
  def _nodeprocessor_language(self, data, parent):
    """Node Processor: language"""
    
    declarations = []
    for node_data in data:
      node = self._process_node(node_data)
      
      if type(node) is str and not node:
        # Will usually happen if comments were in the source
        continue
      
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
        selector_parts[-1] = "%s%s" % ( selector_parts[-1], "".join(selector_item) )
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
    
    oDeclarationBlock = n_DeclarationBlock(parent)
    
    for node_data in data:
      property = self._process_node(node_data, oDeclarationBlock)
      if property and type(property) is str:
        if isinstance(parent, n_Declaration):
          property = self.update_property(property)
        
        oDeclarationBlock.add_property(property)
    
    removed_variable_set = VARIABLE_STACK.pop()
    self._log("V Removing last variable set: %s" % ( str(removed_variable_set), ))
    self._log("V Current Stack: %s" % ( str(VARIABLE_STACK), ))
    
    return oDeclarationBlock
    
  def _nodeprocessor_property(self, data, parent):
    """Node Processor: property"""
    
    name, value = ("", "")
    for property_type, property_item in data:
      if property_type == "propertyname":
        name = property_item.strip()
      elif property_type == "propertyvalue":
        value = property_item.strip()
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
    
    function_name, param_list = ( data[0], [ _[1].strip() for _ in data[1:] if _ and _[1] and _[1].strip() ] )
    fn_name = "".join([ "_directive_", function_name ])
    
    self._log("%s" % ( fn_name ))
    
    if not hasattr(self, fn_name) or not hasattr(getattr(self, fn_name), "__call__"):
      raise Unimplemented("Directive is unimplemented: %s" % ( fn_name, ))
      
    directive_result = getattr(self, fn_name)(parent, *param_list)
    return directive_result
  
  def _nodeprocessor_comment(self, data, parent):
    """Node Processor: comment"""
    
    return ""
    
  def _nodeprocessor_import_rule(self, data, parent):
    """Processor for the '@import url();' rule"""
    
    return n_TextNode(parent, data)
  
  def _nodeprocessor_template(self, data, parent):
    """Define a template that may be reused several times throughout this CSS"""
    
    template_name = data[0]
    params = [ parameter[1] or "" for parameter in data[1:-1] ]
    
    if len(params) == 1 and not params[0]:
      params.pop(0)
    
    dec_block = self._process_node(data[-1], parent=None)
    
    TEMPLATES[template_name] = n_Template(None, template_name, params, dec_block)
    return ""
  
  def _nodeprocessor_use(self, data, parent):
    """Indicate that we with to use a template.
    The template must exist before @@use may be called"""
    
    template_name = data[0]
    params = [ parameter[1] or "" for parameter in data[1:] ]

    if len(params) == 1 and not params[0]:
      params.pop(0)
    
    template = TEMPLATES.get(template_name)
    
    # Verify that this template has been defined
    if not template:
      raise UndefinedTemplate("Template '%s' has not been defined" % ( template_name, ))
      
    # Verify that parameters
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
      p = ""
      for search, replace in param_substitutions:
        pr = property.replace(search, replace)
        if pr != property:
          p = pr
      if p:
        properties.append(self.update_property(p))
      else:
        properties.append(self.update_property(property))
    
    # Add the properties to the parent
    if isinstance(parent, n_DeclarationBlock) and hasattr(parent, "properties"):
      for property in properties:
        parent.add_property(property)
        
    return ""
  
  def _nodeprocessor_expansion(self, data, parent):
    root_name = data[0]
    
    self._update_log_indent(+1)
    self._log("Preparing for the expansion of '%s'" % ( root_name, ))
    
    properties = []
    for node_data in data[1:]:
      node_result = self._process_node(node_data, None)
      
      if not type(node_result) is list:
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
    
    for node_data in data[1:]:
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
    
  def _nodeprocessor_constant(self, data, parent):
    """A constant -- not much to process here"""
    
    if type(data) is str:
      if data.startswith("$"):
        # Return the value. An exception will be raised if the variable doesn't exist!
        return self.get_variable_value(data[1:])
      constant = data
    else:
      raise Unimplemented("expression '%s' in unimplemented" % ( str(data), ))
    
    return constant
    
  #
  # Directives
  #
  
  def _directive_include(self, parent, filename):
    """Include a seperate file, inline, as if all the lines were local
    Returns the processed tree (list) of the parsed AST"""
    
    if type(filename) is str:
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
                       verbose_indent_level=self.log_id + 1)
      
      tree = sm.get_processed_tree()
      if tree:
        for branch in tree:
          branch.parent = parent
          if parent:
            parent.add_child(branch)
        return tree
    return []
  
# ----------------------------------------------------------------------------

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
  
  return arg_parser.parse_args()

if __name__ == '__main__':
  args = get_arguments()
  
  infile = args.infile and args.infile[0] or None
  outfile = args.outfile and args.outfile[0] or None
  
  if args.format in (CSS_OUTPUT_COMPRESSED, CSS_OUTPUT_COMPACT, CSS_OUTPUT_CLEAN):
    output_format = args.format
  else:
    output_format = CSS_OUTPUT_COMPACT
  
  if not args.printcss and not outfile:
    args.printcss = True

  if not infile:
    raise Exception("An input file is required, use -h for help")
  
  try:
    sm = SkidmarkCSS(infile, s_outfile=outfile, verbose=args.verbose, timer=args.timer, printcss=args.printcss, output_format=output_format, show_hierarchy=args.hierarchy)
  except:
    print "-=" * (72/2)
    try:
      raise
    except Unimplemented, e:
      print "%s: %s" % ( e.__class__.__name__, str(e) )
    except UnrecognizedParsedTree, e:
      print "%s: %s" % ( e.__class__.__name__, str(e) )
    except UnexpectedTreeFormat, e:
      print "%s: %s" % ( e.__class__.__name__, str(e) )
    except ErrorInFile, e:
      print "%s: %s" % ( e.__class__.__name__, str(e) )
    except UnrecognizedSelector, e:
      print "%s: %s" % ( e.__class__.__name__, str(e) )
    except FileNotFound, e:
      print "%s: %s" % ( e.__class__.__name__, str(e) )
    except UndefinedTemplate, e:
      print "%s: %s" % ( e.__class__.__name__, str(e) )
    except InvalidTemplateUse, e:
      print "%s: %s" % ( e.__class__.__name__, str(e) )
    except VariableNotFound, e:
      print "%s: %s" % ( e.__class__.__name__, str(e) )
    except Exception, e:
      raise
    finally:
      print "-=" * (72/2)
