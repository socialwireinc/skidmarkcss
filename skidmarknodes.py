# -*- coding: latin-1 -*-

import copy

class SkidmarkHierarchy(object):
  """This is the master class for all skidmark objects.
  Every skidmark object need to derive from this object."""
  
  def __init__(self, parent=None):
    self.parent = parent
    self.children = []
    self._consumed = False
    
  def __repr__(self):
    return "%s__%d" % ( self.__class__.__name__, id(self) )
  
  def clone(self, parent):
    """Clone this object, along with all children in the tree"""
    
    cloned_object = copy.deepcopy(self)
    cloned_object._set_parent_child_relationship(parent)
    return cloned_object
  
  def _set_parent_child_relationship(self, parent):
    """Resets the parents to represent the tree that is passed.
    This is required after a clone because the children are properly
    inherited, but each children is pointing to its previous parent.
    This function runs down the children list and sets the proper
    parent."""
    
    for child in self.iter_children():
      if isinstance(child, SkidmarkHierarchy):
        child.parent = parent
        child._set_parent_child_relationship(child)
    
    return None
  
  def has_parent(self):
    """Returns True or False (it has a parent or not)"""
    
    return not self.parent is None
    
  def has_children(self):
    """Returns True or False (it has child elements or not)"""
    
    return len(self.children) > 0
    
  def add_child(self, child):
    """Add a child to this object"""
    
    self.children.append(child)
    return child
    
  def iter_children(self):
    """Iterate through the object's children elements"""
    
    for child in self.children:
      yield child
    return
    
  def find_child_declaration_blocks(self, current_list=[]):
    """Returns a list of all n_DeclarationBlock() child elements for itself and all descendants"""
    
    for child in self.iter_children():
      if isinstance(child, n_DeclarationBlock):
        # make sure it has properties
        if child:
          current_list.append(child)
      
      if isinstance(child, SkidmarkHierarchy):
        child.find_child_declaration_blocks(current_list)
    return current_list
  
  def find_parent_declarations(self, current_list=[]):
    """Returns a list of all n_Declaration() parent elements for itself and its parent tree"""
    
    if self.has_parent():
      if isinstance(self.parent, n_Declaration):
        current_list.append(self.parent)    
      return self.parent.find_parent_declarations(current_list)
    return current_list
    
  def describe_hierarchy(self, level=0, strings=[]):
    """Returns a list of strings that describes the hierarchy starting from this object.
    Useful for debugging"""
    
    strings.append("    " * level + str(self) + " >>> %d child nodes" % ( len(self.children), ))
    
    for child in self.iter_children():
      if isinstance(child, SkidmarkHierarchy):
        child.describe_hierarchy(level=level + 1, strings=strings)
      else:
        strings.append("    " * (level + 1), " * " + str(child))
    return strings


class n_Declaration(SkidmarkHierarchy):
  """Defines a CSS declaration block"""
  
  def __init__(self, parent):
    SkidmarkHierarchy.__init__(self, parent)
    self.selectors = []
    self.declarationblock = None
  
  def iter_selectors(self):
    """Iterate through the object's selector objects"""
    
    for selector in self.selectors:
      yield selector
    return
  
  def add_selectors(self, selectors):
    """Add selectors (list of selectors) to this object"""
    
    self.selectors.extend(selectors)
    return self.selectors
    
  def set_declarationblock(self, declarationblock):
    """Sets the declarationblock for this object"""
    
    self.declarationblock = declarationblock
    return declarationblock


class n_Selector(SkidmarkHierarchy):
  """Defines a CSS selector"""
  
  def __init__(self, parent, selector):
    SkidmarkHierarchy.__init__(self, parent)
    self.selector = selector
  
  def __repr__(self):
    return "%s : %s" % ( SkidmarkHierarchy.__repr__(self), self.selector )


class n_DeclarationBlock(SkidmarkHierarchy):
  """Defines a CSS declaration block"""
  
  def __init__(self, parent):
    SkidmarkHierarchy.__init__(self, parent)
    self.properties = []
  
  def __nonzero__(self):
    """The object is considered "valid" if it has properties"""
    
    return len(self.properties) > 0
  
  def add_property(self, property):
    """Add a property to the object"""
    
    # Verify if this property already exists, if it does we need to pop it out
    # before appending this new one (this one will essentially crush the previous
    # entry so let's kep the output CSS as clean as possible.
    
    def get_property_name(prop):
      return prop.split(":", 1)[0].strip()
    
    property_name = get_property_name(property)
    property_names = [ get_property_name(prop) for prop in self.properties ]
    
    # If it already exists in the list, remove the original
    if property_name in property_names:
      property_position = property_names.index(property_name)
      self.properties.pop(property_position)
      
    self.properties.append(property)


class n_TextNode(SkidmarkHierarchy):
  """Defines a text node.
  A text node is final, it may not have any children."""
  
  def __init__(self, parent, text):
    SkidmarkHierarchy.__init__(self, parent)
    self.text = text
  
  def __nonzero__(self):
    """The object is considered non-zero if its text is considered non-zero"""
    
    if self.text:
      return True
    return False
    
  def __repr__(self):
    return "%s : %s" % ( SkidmarkHierarchy.__repr__(self), self.text )
  
  def add_child(self, child):
    raise Exception("%s.add_child() is not legal, a text node may not have any children" % ( self.__class__.__name__, ))


class n_Template(SkidmarkHierarchy):
  """Defines a template"""
  
  def __init__(self, parent, name, params, declarationblock):
    SkidmarkHierarchy.__init__(self, parent)
    self.name = name
    self.params = params
    self.declarationblock = declarationblock
  
  def __repr__(self):
    return "%s : %s" % ( SkidmarkHierarchy.__repr__(self), self.name )
  
  def params_are_valid(self, params):
    if len(params) != len(self.params):
      return False
    return True
