# -*- coding: latin-1 -*-

import StringIO
import unittest

import skidmark
from skidmarktestloader import SkidmarkTestLoader

RESULT_TEST_WITHOUT_PROPERTIES = {
  skidmark.skidmarkoutputs.CSS_OUTPUT_COMPRESSED: "",
  skidmark.skidmarkoutputs.CSS_OUTPUT_COMPACT: "",
  skidmark.skidmarkoutputs.CSS_OUTPUT_CLEAN: ""
}

RESULT_TEST_WITH_PROPERTY = {
  skidmark.skidmarkoutputs.CSS_OUTPUT_COMPRESSED: "a{color:#ff0000}",
  skidmark.skidmarkoutputs.CSS_OUTPUT_COMPACT: "a { color: #ff0000; }",
  skidmark.skidmarkoutputs.CSS_OUTPUT_CLEAN: "a {\n\\scolor: #ff0000;\n}"
}

RESULT_TEST_WITH_PROPERTIES = {
  skidmark.skidmarkoutputs.CSS_OUTPUT_COMPRESSED: "a{color:red;text-decoration:none}",
  skidmark.skidmarkoutputs.CSS_OUTPUT_COMPACT: "a { color: red; text-decoration: none; }",
  skidmark.skidmarkoutputs.CSS_OUTPUT_CLEAN: "a {\n\\scolor: red;\n\\stext-decoration: none;\n}"
}

class TestSingleSelector(unittest.TestCase, SkidmarkTestLoader):
  def setUp(self):
    self.config = dict(
      verbose=False,
      timer=False,
      printcss=False,
      show_hierarchy=False,
      simplify_output=True,
      unify_selectors=True
    )
    return
  
  def test_without_properties(self):
    results = self.get_test_results(self.config, "singleselector_withoutproperties.sm")
    
    for style, expected_result in RESULT_TEST_WITHOUT_PROPERTIES.iteritems():
      res = self.get_style_result(style, results)
      self.assertTrue(res == self.normalize_string(expected_result).replace("\\s", " " * skidmark.skidmarkoutputs.SPACING_CLEAN))
    
    return
  
  def test_with_property(self):
    results = self.get_test_results(self.config, "singleselector_withproperty.sm")
    
    for style, expected_result in RESULT_TEST_WITH_PROPERTY.iteritems():
      res = self.get_style_result(style, results)
      self.assertTrue(res == self.normalize_string(expected_result).replace("\\s", " " * skidmark.skidmarkoutputs.SPACING_CLEAN))
    
    return
  
  def test_with_properties(self):
    results = self.get_test_results(self.config, "singleselector_withproperties.sm")

    
    for style, expected_result in RESULT_TEST_WITH_PROPERTIES.iteritems():
      res = self.get_style_result(style, results)
      self.assertTrue(res == self.normalize_string(expected_result).replace("\\s", " " * skidmark.skidmarkoutputs.SPACING_CLEAN))

    return
  
  def tearDown(self):
    pass
