# -*- coding: latin-1 -*-

SPACING_CLEAN = 2

CSS_OUTPUT_COMPRESSED = 0
CSS_OUTPUT_COMPACT = 1
CSS_OUTPUT_CLEAN = 2
CSS_OUTPUT_SINGLELINE = 3

OUTPUT_TEMPLATE_DECLARATION = {
  CSS_OUTPUT_SINGLELINE: "%s{%s}",
  CSS_OUTPUT_COMPRESSED: "%s{%s}",
  CSS_OUTPUT_COMPACT: "%s { %s; }",
  CSS_OUTPUT_CLEAN: "%%s {\n%s%%s;\n}\n" % ( " " * SPACING_CLEAN, )
}

OUTPUT_TEMPLATE_SELECTOR_SEPARATORS = {
  CSS_OUTPUT_SINGLELINE: ",",
  CSS_OUTPUT_COMPRESSED: ",",
  CSS_OUTPUT_COMPACT: ", ",
  CSS_OUTPUT_CLEAN: ",\n"
}

OUTPUT_TEMPLATE_PROPERTY_SEPARATORS = {
  CSS_OUTPUT_SINGLELINE: ";",
  CSS_OUTPUT_COMPRESSED: ";",
  CSS_OUTPUT_COMPACT: "; ",
  CSS_OUTPUT_CLEAN: ";\n%s" % ( " " * SPACING_CLEAN, )
}

OUTPUT_TEMPLATE_PROPERTY_VALUE_SEPARATOR = {
  CSS_OUTPUT_SINGLELINE: ":",
  CSS_OUTPUT_COMPRESSED: ":",
  CSS_OUTPUT_COMPACT: ": ",
  CSS_OUTPUT_CLEAN: ": "
}

OUTPUT_TEMPLATE_COMBINATOR = {
  CSS_OUTPUT_SINGLELINE: "%s",
  CSS_OUTPUT_COMPRESSED: "%s",
  CSS_OUTPUT_COMPACT: " %s",
  CSS_OUTPUT_CLEAN: " %s"
}

OUTPUT_TEMPLATE_DECLARATION_SEPARATOR = {
  CSS_OUTPUT_SINGLELINE: "",
  CSS_OUTPUT_COMPRESSED: "\n",
  CSS_OUTPUT_COMPACT: "\n",
  CSS_OUTPUT_CLEAN: "\n"
}

OUTPUT_TEMPLATE_MEDIAQUERY = {
  CSS_OUTPUT_SINGLELINE: "%s{%s}",
  CSS_OUTPUT_COMPRESSED: "%s{%s}",
  CSS_OUTPUT_COMPACT: "%s { %s }",
  CSS_OUTPUT_CLEAN: "%%s {\n%s%%s\n}\n" % ( " " * SPACING_CLEAN, )
}
