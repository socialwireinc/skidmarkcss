# -*- coding: latin-1 -*-

class SkidmarkHierarchy(object):
  def __init__(self, parent=None):
    self.parent = parent
    self.children = []
    self._consumed = False
    
  def __repr__(self):
    return "%s__%d" % ( self.__class__.__name__, id(self) )
    
  def _represent(self):
    raise Unimplemented("The _represent() method has not been implemented for %s" % ( str(self), ))
    
  def has_parent(self):
    return not self.parent is None
    
  def has_children(self):
    return len(self.children) > 0
    
  def add_child(self, child):
    self.children.append(child)
    return child
    
  def iter_children(self):
    for child in self.children:
      yield child
    return


class n_Declaration(SkidmarkHierarchy):
  def __init__(self, parent):
    SkidmarkHierarchy.__init__(self, parent)
    self.selectors = []
    self.declarationblock = None
  
  def _represent(self):
    # We have a single declaration block, but the properties from this declaration
    # block may be other n_Declaration objects. Those need to be handled here. We need
    # to recurse through ALL the children to identify the whole tree in order
    # to identify all elements at play.
    
    declarations = list(set(self._retrieve_declaration_tree()))
    return "\n".join(declarations)
  
  def _retrieve_declaration_tree(self, selectors=[], current_declarations=[]):
    # Returns a list of declarations
    properties = []
    
    for property in self.declarationblock.properties:
      if isinstance(property, n_Declaration):
        current_declarations.extend(property._retrieve_declaration_tree(selectors + self.selectors, current_declarations))
      else:
        properties.append(property)
    
    if properties:
      current = [ selector._represent() for selector in selectors ]
      passed = [ selector._represent() for selector in self.selectors ]
      
      all_selectors = []
      if current:
        for c in current:
          for p in passed:
            all_selectors.append(c + " " + p)
      else:
        all_selectors = passed
      
      declaration = "%s { %s; }" % ( ", ".join(all_selectors), "; ".join(properties) )
      current_declarations.append(declaration)
    
    return current_declarations
  
  def add_selectors(self, selectors):
    self.selectors.extend(selectors)
    return self.selectors
    
  def set_declarationblock(self, declarationblock):
    self.declarationblock = declarationblock
    return declarationblock


class n_Selector(SkidmarkHierarchy):
  def __init__(self, parent, selector):
    SkidmarkHierarchy.__init__(self, parent)
    self.selector = selector
    
  def _represent(self):
    return self.selector


class n_DeclarationBlock(SkidmarkHierarchy):
  def __init__(self, parent):
    SkidmarkHierarchy.__init__(self, parent)
    self.properties = []
  
  def __nonzero__(self):
    return len(self.properties) > 0
  
  def add_property(self, property):
    self.properties.append(property)
  
  def _represent(self):
    print "properties = ", self.properties
    return "{}"
