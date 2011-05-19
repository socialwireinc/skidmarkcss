# -*- coding: latin-1 -*-

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

CSS_OUTPUT_COMPRESSED = 0
CSS_OUTPUT_COMPACT = 1
CSS_OUTPUT_CLEAN = 2

OUTPUT_TEMPLATE_DECLARATION = {
  CSS_OUTPUT_COMPRESSED : "%s{%s;}",
  CSS_OUTPUT_COMPACT : "%s { %s; }",
  CSS_OUTPUT_CLEAN : "%s {\n    %s;\n}\n"
}

OUTPUT_TEMPLATE_SELECTOR_SEPARATORS = {
  CSS_OUTPUT_COMPRESSED : ",",
  CSS_OUTPUT_COMPACT : ", ",
  CSS_OUTPUT_CLEAN : ",\n"
}

OUTPUT_TEMPLATE_PROPERTY_SEPARATORS = {
  CSS_OUTPUT_COMPRESSED : ";",
  CSS_OUTPUT_COMPACT : "; ",
  CSS_OUTPUT_CLEAN : ";\n    "
}

class SkidmarkCSS(object):
  def __init__(self, s_infile, s_outfile=None, verbose=True, timer=False, printcss=False, output_format=CSS_OUTPUT_COMPRESSED):
    """Create the object by specifying a filename (s_infile) as an argument (string)"""
    
    start_time = time.time()
    
    self.s_infile = s_infile
    self.s_outfile = s_outfile
    self.verbose = verbose
    self.printcss = printcss
    self.output_format = output_format
    self.log_id = 0
    self.src = ""
    self.ast = self._parse_file()
    self.processed_tree = self._process()
    
    if timer:
      self.verbose = True
      self._log("Elapsed Time: %.04f" % ( time.time() - start_time, ))
      self.verbose = verbose
    
    return
    
  def get_processed_tree(self):
    """Return the object's processed tree"""
    
    return self.processed_tree
  
  def _log(self, s, leading=0):
    """Print strings to the screen, for debugging"""
    
    if self.verbose:
      if type(leading) is int and leading:
        print "%s%s" % ( "  " * (leading * 2), s )
      else:
        print s
    return
    
  def _parse_file(self):
    """Parses the data using pyPEG, according to the Skidmark Language definition"""
    
    self._log("-" * 72)
    self._log("Loading '%s'" % ( self.s_infile, ))
    self.src = self._get_file_src()
    
    self._log("%ld bytes" % ( len(self.src), ), leading=1)
    self._log("Using pyPEG to obtain the AST", leading=1)
    return pyPEG.parseLine(self.src, skidmarklanguage.language, resultSoFar=[], skipWS=True)
  
  def _get_file_src(self):
    """Reads the byte content of self.s_infile and returns it as a string"""
    
    self._log("Reading file contents", leading=1)
    
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
    
    self._log("\nWalking through the AST to create an object tree")
    data = self._process_node(tree[0])
    self._log("Walking through as has completed")
    
    if self.verbose:
      self._log("\nGenerated the following hierarchy")
      description = []
      for node in data:
        description = node.describe_hierarchy(0, description)
      for desc in description:
        self._log(desc, leading=1)
    
    css = self._generate_css(data)
    if self.verbose:
      self._log("\nGenerated CSS")
      for css_line in css:
        self._log(css_line, leading=1)
    
    self._create_outfile("\n".join(css))
      
    self._log("=" * 72)
    self._log("Loading Completed")
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
          
        all_selectors = [ " ".join(s) for s in self._simplyfy_selectos(itertools.product(*selectors)) ]
        
        css.append(OUTPUT_TEMPLATE_DECLARATION[self.output_format] % (
          OUTPUT_TEMPLATE_SELECTOR_SEPARATORS[self.output_format].join(all_selectors),
          OUTPUT_TEMPLATE_PROPERTY_SEPARATORS[self.output_format].join(blk.properties)
        ))
    
    return css
  
  def _simplyfy_selectos(self, selectors):
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
    
    self._log("Generating %s" % ( self.s_outfile or "CSS to stdout", ))
    
    if self.s_outfile:
      open(self.s_outfile, "wt").write(css_text)
    
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
    self._log("@%s" % ( fn_name, ), leading=self.log_id)
    self._log("P = %s" % ( parent, ), leading=self.log_id)
    
    if not hasattr(self, fn_name) or not hasattr(getattr(self, fn_name), "__call__"):
      raise Unimplemented("Node type is unimplemented: %s" % ( fn_name, ))
    
    processor_result = getattr(self, fn_name)(node[1], parent)
    self._log(">>> Generated '%s'" % ( processor_result, ), leading=self.log_id + 1)
    
    if type(processor_result) is list:
      for pr in processor_result:
        if isinstance(parent, SkidmarkHierarchy) and isinstance(pr, SkidmarkHierarchy):
          parent.add_child(pr)
    else:
      if isinstance(parent, SkidmarkHierarchy) and isinstance(processor_result, SkidmarkHierarchy):
        parent.add_child(processor_result)
    
    self.log_id -= 1
    return processor_result
  
  
  #
  # Node Processors: What interprets the AST
  #
  
  def _nodeprocessor_language(self, data, parent):
    """Node Processor: language"""
    
    declarations = []
    for node_data in data:
      node = self._process_node(node_data)
      
      if type(node) is str and not node:
        # Will usually happen in comments were in the source
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
    
    while data:
      current_element = data.pop(0)
      selector_type, selector_item = current_element
      
      if selector_type == "element_name":
        selector_parts.append(selector_item)
      elif selector_type == "pseudo":
        for pseudo_type, pseudo_item in selector_item:
          if pseudo_type == "ident":
            if selector_parts:
              selector_parts[-1] = "%s:%s" % ( selector_parts[-1], pseudo_item )
            else:
              selector_parts.append(":" + pseudo_item)
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
      else:
        raise UnrecognizedSelector(selector_type + ":" + str(selector_item))
      
    return selector_parts
  
  def _nodeprocessor_declarationblock(self, data, parent):
    """Node Processor: declarationblock"""
    
    oDeclarationBlock = n_DeclarationBlock(parent)
    
    for node_data in data:
      node_result = self._process_node(node_data, oDeclarationBlock)
      if node_result and type(node_result) is str:
        oDeclarationBlock.add_property(node_result)
    
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
    return "%s: %s" % ( name, value )
  
  def _nodeprocessor_property_unterminated(self, data, parent):
    """Node Processor: property_unterminated"""
    
    return self._nodeprocessor_property(data, parent)
  
  def _nodeprocessor_directive(self, data, parent):
    """Node Processor: directive"""
    
    function_name, param_list = ( data[0], [ _[1].strip() for _ in data[1:] if _ and _[1] and _[1].strip() ] )
    fn_name = "".join([ "_directive_", function_name ])
    
    self._log("%s" % ( fn_name ), leading=self.log_id)
    
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
      sm = SkidmarkCSS(filename, s_outfile=None, verbose=self.verbose)
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
  arg_parser.add_argument("-i", "--input", dest="infile", help="The input file", nargs=1)
  arg_parser.add_argument("-o", "--output", dest="outfile", help="The output file", nargs=1)
  arg_parser.add_argument("-v", "--verbose", dest="verbose", help="Display detailed information", action="store_true")
  arg_parser.add_argument("-p", "--printcss", dest="printcss", help="Output the final CSS to stdout", action="store_true")
  arg_parser.add_argument("-t", "--timer", dest="timer", help="Display timer information", action="store_true")
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
    sm = SkidmarkCSS(infile, s_outfile=outfile, verbose=args.verbose, timer=args.timer, printcss=args.printcss, output_format=output_format)
  except:
    print "=" * 72
    try:
      raise
    except Unimplemented, e:
      print e
    except UnrecognizedParsedTree, e:
      print e
    except ErrorInFile, e:
      print e
    except UnrecognizedSelector, e:
      print e
    except FileNotFound, e:
      print "File Not Found: " + str(e)
    except Exception, e:
      raise
    finally:
      print "=" * 72
