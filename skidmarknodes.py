# -*- coding: latin-1 -*-

class SkidmarkHierarchy(object):
  def __init__(self, parent=None):
    self.parent = parent
    self.children = []
    self._consumed = False
    
  def __repr__(self):
    return "%s__%d" % ( self.__class__.__name__, id(self) )
    
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
    
  def find_child_declaration_blocks(self, current_list=[]):
    for child in self.iter_children():
      if isinstance(child, n_DeclarationBlock):
        # make sure it has properties
        if child:
          current_list.append(child)
      
      if isinstance(child, SkidmarkHierarchy):
        child.find_child_declaration_blocks(current_list)
    return current_list
  
  def find_parent_declarations(self, current_list=[]):
    if self.has_parent():
      if isinstance(self.parent, n_Declaration):
        current_list.append(self.parent)    
      return self.parent.find_parent_declarations(current_list)
    return current_list
    
  def describe_hierarchy(self, level=0, strings=[]):
    strings.append("    " * level + str(self) + " >>> %d child nodes" % ( len(self.children), ))
    
    for child in self.iter_children():
      if isinstance(child, SkidmarkHierarchy):
        child.describe_hierarchy(level=level + 1, strings=strings)
      else:
        strings.append("    " * (level + 1), " * " + str(child))
    return strings


class n_Declaration(SkidmarkHierarchy):
  def __init__(self, parent):
    SkidmarkHierarchy.__init__(self, parent)
    self.selectors = []
    self.declarationblock = None
  
  def iter_selectors(self):
    for selector in self.selectors:
      yield selector
    return
  
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
  
  def __repr__(self):
    return "%s : %s" % ( SkidmarkHierarchy.__repr__(self), self.selector )


class n_DeclarationBlock(SkidmarkHierarchy):
  def __init__(self, parent):
    SkidmarkHierarchy.__init__(self, parent)
    self.properties = []
  
  def __nonzero__(self):
    return len(self.properties) > 0
  
  def add_property(self, property):
    self.properties.append(property)
