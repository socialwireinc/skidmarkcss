# -*- coding: latin-1 -*-

import re
import pyPEG
import skidmarklanguage

from skidmarknodes import *

class FileNotFound(Exception): pass
class UnrecognizedParsedTree(Exception): pass
class UnrecognizedSelector(Exception): pass
class Unimplemented(Exception): pass
class ErrorInFile(Exception): pass
class UnexpectedTreeFormat(Exception): pass

class SkidmarkCSS(object):
  def __init__(self, s_infile, s_outfile="outfile.css", quiet=False):
    """Create the object by specifying a filename (s_infile) as an argument (string)"""
    self.s_infile = s_infile
    self.s_outfile = s_outfile
    self.quiet = quiet
    self.log_id = 0
    self.src = ""
    self.ast = self._parse_file()
    self.processed_tree = self._process()
    return
    
  def get_processed_tree(self):
    return self.processed_tree
  
  def _log(self, s, leading=0):
    if not self.quiet:
      if type(leading) is int and leading:
        print "%s%s" % ( "  " * leading, s )
      else:
        print s
    return
    
  def _parse_file(self):
    """Parses the data using pyPEG, according to the Skidmark Language definition"""
    
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
    
    self._log("Processing AST")
    data = self._process_node(tree[0])
    
    self._log("")
    self._log("DESCRIBING HIERARCHY")
    self._log("")
    
    for node in data:
      description = node.describe_hierarchy()
    print "\n".join(description)
    
    css = self._generate_css(data)
    
    if self.s_outfile:
      self._create_outfile(css)
    return data
    
  def _generate_css(self, tree):
    # The outer level of the tree should be a list
    if not type(tree) is list:
      raise UnexpectedTreeFormat("The tree format passed to the _generate_css() method is nor recognized")
    
    css = []
    for node in tree:
      if isinstance(node, n_Declaration):
        # We only expect this node at the top level!
        css.append(node._represent())
      else:
        print 'NOOOOOOOOOOOOOOOOOOOOOOO'
        print type(node)
        print node
    
    return "\n".join(css)
    
  def _create_outfile(self, css_text):
    """Generates the output file (self.s_outfile)"""
    
    self._log("Generating %s" % ( self.s_outfile, ))
    open(self.s_outfile, "wt").write(css_text)
    return
  
  def _process_node(self, node, parent=None):
    """Process a single node from the AST"""
    
    self.log_id = self.log_id + 1
    
    node_len = len(node)
    if node_len != 2:
      raise UnrecognizedParsedTree("Nodes should only have 2 elements, not %d: %s" % ( node_len, str(node) ))
    
    fn_name = "".join([ "_nodeprocessor_", node[0] ])
    self._log("@%s" % ( fn_name, ), leading=self.log_id)
    self._log("P = %s" % ( parent, ), leading=self.log_id)
    
    if not hasattr(self, fn_name) or not hasattr(getattr(self, fn_name), "__call__"):
      raise Unimplemented("Node type is unimplemented: %s" % ( fn_name, ))
      
    processor_result = getattr(self, fn_name)(node[1], parent)
    self._log(">>> Generated '%s'" % ( processor_result, ), leading=self.log_id + 1)
    
    if isinstance(parent, SkidmarkHierarchy) and isinstance(processor_result, SkidmarkHierarchy):
      parent.add_child(processor_result)
    
    self.log_id = self.log_id - 1
    return processor_result
  
  
  #
  # Node Processors: What interprets the AST
  #
  
  def _nodeprocessor_language(self, data, parent):
    declarations = []
    for node_data in data:
      declarations.append(self._process_node(node_data))
    return declarations
  
  def _nodeprocessor_declaration(self, data, parent):
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
    selector_parts = []
    for selector_type, selector_item in data:
      if selector_type == "element_name":
        selector_parts.append(selector_item)
      elif selector_type == "pseudo":
        for pseudo_type, pseudo_item in selector_item:
          if pseudo_type == "ident":
            selector_parts.append(":" + pseudo_item)
          elif pseudo_type == "function":
            raise Unimplemented("%s has not yet been implemented" % ( str(selector_item), ))
      else:
        raise UnrecognizedSelector(selector_type)
        
    return n_Selector(parent, "".join(selector_parts))
  
  def _nodeprocessor_declarationblock(self, data, parent):
    oDeclarationBlock = n_DeclarationBlock(parent)
    
    for node_data in data:
      node_result = self._process_node(node_data, oDeclarationBlock)
      if node_result and not isinstance(node_result, SkidmarkHierarchy):
        oDeclarationBlock.add_property(node_result)
    
    return oDeclarationBlock
    
  def _nodeprocessor_property(self, data, parent):
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
    return self._nodeprocessor_property(data, parent)
  
  def _nodeprocessor_directive(self, data, parent):
    function_name, param_list = ( data[0], [ _[1].strip() for _ in data[1:] if _ and _[1] and _[1].strip() ] )
    fn_name = "".join([ "_directive_", function_name ])
    
    self._log("%s" % ( fn_name ), leading=self.log_id)
    
    if not hasattr(self, fn_name) or not hasattr(getattr(self, fn_name), "__call__"):
      raise Unimplemented("Directive is unimplemented: %s" % ( fn_name, ))
      
    directive_result = getattr(self, fn_name)(parent, *param_list)
    return directive_result
  
  def _nodeprocessor_comment(self, data):
    return ""
  
  
  #
  # Directives
  #
  
  def _directive_include(self, parent, filename):
    if type(filename) is str:
      if filename.startswith('"') and filename.endswith('"'):
        filename = filename[1:-1]
      elif filename.startswith("'") and filename.endswith("'"):
        filename = filename[1:-1]
        
      # Include the file by instantiating a new object to process it
      sm = SkidmarkCSS(filename, s_outfile=None, quiet=True)
      return "\n".join(sm.get_processed_tree())
    return ""
  
# ----------------------------------------------------------------------------

if __name__ == '__main__':
  try:
    sm = SkidmarkCSS("sample.smcss", s_outfile="sample.css", quiet=False)
    #print "\n".join(sm.get_processed_tree())
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
      print e
    except Exception, e:
      raise
    finally:
      print "=" * 72
