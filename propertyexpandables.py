# -*- coding: latin-1 -*-

PROPERTY_EXPANDABLES = {
  #
  # border-radius
  #
  "border-radius": [
    "-moz-border-radius",
    "-webkit-border-radius"
  ],
  "border-top-left-radius": [
    "-moz-border-radius-topleft",
    "-webkit-border-top-left-radius"
  ],
  "border-top-right-radius": [
    "-moz-border-radius-topright",
    "-webkit-border-top-right-radius"
  ],
  "border-bottom-left-radius": [
    "-moz-border-radius-bottomleft",
    "-webkit-border-bottom-left-radius"
  ],
  "border-bottom-right-radius": [
    "-moz-border-radius-bottomright",
    "-webkit-border-bottom-right-radius"
  ]
}

PROPERTY_SHORTHANDS = {
  "padding": [
    [ "padding-top", "padding-right", "padding-bottom", "padding-left" ],
  ],
  "margin": [
    [ "margin-top", "margin-right", "margin-bottom", "margin-left" ],
  ]
}

PROPERTIES_AVAILABLE_FOR_SHORTHAND = []
for block_lists in PROPERTY_SHORTHANDS.values():
  for block in block_lists:
    PROPERTIES_AVAILABLE_FOR_SHORTHAND.extend(block)
PROPERTIES_AVAILABLE_FOR_SHORTHAND = list(set(PROPERTIES_AVAILABLE_FOR_SHORTHAND))
