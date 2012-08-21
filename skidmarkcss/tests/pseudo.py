# -*- coding: latin-1 -*-

import StringIO
import unittest

import skidmark
from skidmarktestloader import SkidmarkTestLoader

RESULT_PSEUDO1 = {
  skidmark.skidmarkoutputs.CSS_OUTPUT_COMPRESSED: "a:link{color:red}",
  skidmark.skidmarkoutputs.CSS_OUTPUT_COMPACT: "a:link { color: red; }",
  skidmark.skidmarkoutputs.CSS_OUTPUT_CLEAN: "a:link {\n\\scolor: red;\n}"
}

RESULT_PSEUDO2 = {
  skidmark.skidmarkoutputs.CSS_OUTPUT_COMPRESSED: "a::link{color:red}",
  skidmark.skidmarkoutputs.CSS_OUTPUT_COMPACT: "a::link { color: red; }",
  skidmark.skidmarkoutputs.CSS_OUTPUT_CLEAN: "a::link {\n\\scolor: red;\n}"
}

class TestPseudo(unittest.TestCase, SkidmarkTestLoader):
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
  
  def test_pseudo1(self):
    results = self.get_test_results(self.config, "pseudo_pseudo1.sm")
    
    for style, expected_result in RESULT_PSEUDO1.iteritems():
      res = self.get_style_result(style, results)
      self.assertTrue(res == self.normalize_string(expected_result).replace("\\s", " " * skidmark.skidmarkoutputs.SPACING_CLEAN))
    
    return
  
  def test_pseudo2(self):
    results = self.get_test_results(self.config, "pseudo_pseudo2.sm")
    
    for style, expected_result in RESULT_PSEUDO2.iteritems():
      res = self.get_style_result(style, results)
      self.assertTrue(res == self.normalize_string(expected_result).replace("\\s", " " * skidmark.skidmarkoutputs.SPACING_CLEAN))
    
    return
  
  def tearDown(self):
    pass
