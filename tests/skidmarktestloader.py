# -*- coding: latin-1 -*-

import os.path
import StringIO

import skidmark

TEST_STYLES = [
  skidmark.skidmarkoutputs.CSS_OUTPUT_COMPRESSED,
  skidmark.skidmarkoutputs.CSS_OUTPUT_COMPACT,
  skidmark.skidmarkoutputs.CSS_OUTPUT_CLEAN
]

class SkidmarkTestLoader(object):
  def __init__(self):
    self.file = None
    self.config = dict()
  
  def update_output_style(self, output_style):
    self.config["output_format"] = output_style
    return
  
  def get_test_results(self, config, test_file):
    results = []
    
    for style in TEST_STYLES:
      sio_file = StringIO.StringIO()
      self.update_output_style(style)
      skidmark.SkidmarkCSS(self.config, self.load_file(test_file), sio_file)
      results.append(self.get_result(sio_file))
    
    return results
  
  def load_file(self, filepath):
    path = os.path.join("tests", "testfiles", filepath)
    self.file = StringIO.StringIO(open(path, "rb").read())
    return self.file
  
  def get_result(self, stringio_obj):
    return self.normalize_string(stringio_obj.getvalue())
  
  def get_style_result(self, style, results):
    return results[TEST_STYLES.index(style)]
  
  def normalize_string(self, string):
    return string.strip().replace("\r\n", "\n")
