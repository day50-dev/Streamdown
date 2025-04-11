#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "pylatexenc"
# ]
# ///
from pylatexenc.latex2text import LatexNodes2Text

class Parser:
  inState = False
  buffer = ''

def Plugin(text, state = None, style = None):
  res = True
  if not Parser.inState:
    if '$$' in text:
      Parser.buffer = ''
      Parser.inState = True
      text = text[text.index('$$') + 2:]

  if Parser.inState:
    if not '$$' in text:
      Parser.buffer += text
      return res 

    Parser.inState = False
    Parser.buffer += text[:text.index('$$')]

    return [LatexNodes2Text().latex_to_text(Parser.buffer)]

