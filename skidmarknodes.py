# -*- coding: latin-1 -*-

"""Definition for all the node objects, converted from the pyPEG AST"""

import copy

from propertyexpandables import PROPERTY_EXPANDABLES, PROPERTY_SHORTHANDS, ShorthandHandler, ExpandableHandler

class SkidmarkHierarchy(object):
  """This is the master class for all skidmark objects.
  Every skidmark object need to derive from this object."""
  
  def __init__(self, parent=None):
    self.parent = parent
    self.children = []
    
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
    inherited, but each child is pointing to its previous parent.
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
    
    # Required because the 'include' method sets the parent/child relationships before
    # passing the results back to the node_processor, which then handles the nodes. It 
    # may happend that a child is added to the same parent a second time.
    if not id(child) in [ id(c) for c in self.children ]:
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
  
  def __init__(self, parent, simplify_output):
    SkidmarkHierarchy.__init__(self, parent)
    self.properties = []
    self.simplify_output = simplify_output
    self.requires_shorthand_check = False
  
  def __nonzero__(self):
    """The object is considered "valid" if it has properties"""
    
    return len(self.properties) > 0
  
  def _expand_property(self, property_name):
    """Returns a list of alias property names that should also be set to the same value"""
    
    expandables = [ property_name ] + PROPERTY_EXPANDABLES.get(property_name, [])
    return expandables
  
  def add_property(self, property, bypass_expand=False, position=-1):
    """Add a property to the declaration block"""
    
    # Verify if this property already exists, if it does we need to pop it out
    # before appending the new one. This property will essentially crush the
    # previous one and keep the output CSS as clean as possible.
    
    prop_name, prop_value = n_DeclarationBlock.get_property_parts(property)
    
    if self.simplify_output and not bypass_expand and ShorthandHandler.is_shorthand(prop_name):
      properties_to_add = ShorthandHandler.expand_shorthand(prop_name, prop_value)
      
      if properties_to_add:
        for p_name, p_value in properties_to_add:
          if p_value is None:
            self.remove_property(p_name)
          else:
            new_property = "%s: %s" % ( p_name, p_value )
            self.add_property(new_property)
        
        return
    
    expanded_property_names = n_DeclarationBlock._expand_property(self, prop_name)
    property_names = [ n_DeclarationBlock.get_property_parts(prop)[0] for prop in self.properties ]
    
    props_available_for_shorthand = ShorthandHandler.get_properties_available_for_shorthand()
    # If it already exists in the list, remove the original
    for property_name in expanded_property_names:
      if not self.requires_shorthand_check and property_name in props_available_for_shorthand:
        self.requires_shorthand_check = True
      
      if property_name in property_names:
        property_position = property_names.index(property_name)
        self.properties.pop(property_position)
      
      if callable(property_name):
        new_property = property_name(prop_value)
      else:
        new_property = property.replace(prop_name, property_name)
      
      if position >= 0:
        self.properties.insert(position, new_property)
      else:
        self.properties.append(new_property)
    
    return
  
  def remove_property(self, property_name):
    """Remove a property, by name.  The method does not indicate whether or not
    a property was actually removed (in the case where it never existed to be removed).
    Returns the properties, post removal."""
    
    active_properties = [ n_DeclarationBlock.get_property_parts(prop)[0] for prop in self.properties ]
    to_remove = []
    
    if type(property_name) is list:
      for p_name in property_name:
        if p_name in active_properties:
          to_remove.append(active_properties.index(p_name))      
    else:
      if property_name in active_properties:
        to_remove.append(active_properties.index(property_name))
    
    if to_remove:
      to_remove.sort()
      while to_remove:
        idx = to_remove.pop()
        self.properties.pop(idx)
    
    return self.properties
  
  def has_property(self, property_name):
    """Check whether or not a property exists.  If so, the property's
    value is returned, None is returned oterwise"""
    
    for prop in self.properties:
      p_name, p_value = n_DeclarationBlock.get_property_parts(prop)
      if p_name == property_name:
        return p_value
    
    return None
  
  def simplify_shorthandables(self):
    """Scan through the properties to determine if it is possible to regroup
    the entries into shorthand syntax.  This method will take care of updating
    the properties itself and does not return anything.
    
    I decided that 'shorthandables' was a word.  Use it at will."""
    
    # Scan through the properties. Everytime we find a shorthand version, verify
    # all properties defined beforehand to see if they contain property names that
    # this shorthand would overwrite. If this is the case, keep track of these
    # properties so that we can remove them after.
    to_remove = set()
    processed = []
    for property in self.properties:
      prop_name, prop_value = n_DeclarationBlock.get_property_parts(property)
      if ShorthandHandler.is_shorthand(prop_name):
        props_to_nuke = ShorthandHandler.get_all_expand_properties(prop_name)
        for p_nuke in props_to_nuke:
          if p_nuke in processed:
            to_remove.add(processed.index(p_nuke))
      
      processed.append(prop_name)
    
    # Remove the properties that would get overwritten.
    if to_remove:
      to_remove = list(to_remove)
      to_remove.sort()
      
      for idx in to_remove[::-1]:
        self.properties.pop(idx)
        processed.pop(idx)
    
    # Create the shorthand if it's possible (removing the originals)
    for shorthand, shorthand_blocks in PROPERTY_SHORTHANDS.iteritems():
      for blk in shorthand_blocks:
        style = blk[0]
        block_values = [ self.has_property(property_name) for property_name in blk[1:] ]
        shorthand_property = ShorthandHandler.process(style, shorthand, block_values)
        if shorthand_property:
          properties_to_check = [ p_name for p_name in ShorthandHandler.get_all_expand_properties(shorthand) if p_name not in blk[1:] ]
          positions = [ processed.index(p_name) for p_name in properties_to_check if p_name in processed ] + [-1]
          
          self.add_property(shorthand_property, bypass_expand=True, position=positions[0])
          self.remove_property(blk)
          break
    
    return
  
  @classmethod
  def get_property_parts(cls, prop):
    """Split the propername and and property value"""
    
    name, value = [ ps.strip() for ps in prop.split(":", 1) ]
    return name, value


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
