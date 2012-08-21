# -*- coding: latin-1 -*-

import StringIO
import unittest

import skidmark
from skidmarktestloader import SkidmarkTestLoader

RESULT_TEST_INHERITANCE_SIMPLE = {
  skidmark.skidmarkoutputs.CSS_OUTPUT_COMPRESSED: "a:link{color:red}",
  skidmark.skidmarkoutputs.CSS_OUTPUT_COMPACT: "a:link { color: red; }",
  skidmark.skidmarkoutputs.CSS_OUTPUT_CLEAN: "a:link {\n\\scolor: red;\n}"
}

RESULT_TEST_INHERITANCE_COMPOUND = {
  skidmark.skidmarkoutputs.CSS_OUTPUT_COMPRESSED: "ul.test{display:none}\nul.test li{color:green}\nul li{padding:8px}\nul li.first{padding:0}",
  skidmark.skidmarkoutputs.CSS_OUTPUT_COMPACT: "ul.test { display: none; }\nul.test li { color: green; }\nul li { padding: 8px; }\nul li.first { padding: 0; }",
  skidmark.skidmarkoutputs.CSS_OUTPUT_CLEAN: "ul.test {\n\\sdisplay: none;\n}\n\nul.test li {\n\\scolor: green;\n}\n\nul li {\n\\spadding: 8px;\n}\n\nul li.first {\n\\spadding: 0;\n}"
}

class TestInheritance(unittest.TestCase, SkidmarkTestLoader):
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
  
  def test_inheritance_simple(self):
    results = self.get_test_results(self.config, "inheritance_simple.sm")
    
    for style, expected_result in RESULT_TEST_INHERITANCE_SIMPLE.iteritems():
      res = self.get_style_result(style, results)
      exp = self.normalize_string(expected_result).replace("\\s", " " * skidmark.skidmarkoutputs.SPACING_CLEAN)
      self.assertTrue(res == exp)
    
    return
  
  def test_inheritance_compound(self):
    results = self.get_test_results(self.config, "inheritance_compound.sm")
    
    for style, expected_result in RESULT_TEST_INHERITANCE_COMPOUND.iteritems():
      res = self.get_style_result(style, results)
      exp = self.normalize_string(expected_result).replace("\\s", " " * skidmark.skidmarkoutputs.SPACING_CLEAN)
      self.assertTrue(res == exp)
    
    return
  
  def tearDown(self):
    pass
