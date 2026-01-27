#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "pylatexenc"
# ]
# ///
from pylatexenc.latex2text import LatexNodes2Text

converter = LatexNodes2Text()

class Parser:
  inState = False
  end = ''
  buffer = ''
  prefix = ''
  mode = None

def Plugin(text, state = None, style = None):
  res = True
  had_conversion = False
  tokens = [
    ('$$', '$$', 'block'),
    ('\\[', '\\]', 'block'),
    ('\\(', '\\)', 'inline'),
  ]

  if Parser.inState:
    if Parser.end not in text:
      Parser.buffer += text
      return res

    before, after = text.split(Parser.end, 1)
    Parser.buffer += before
    converted = converter.latex_to_text(Parser.buffer)
    prefix = Parser.prefix
    mode = Parser.mode

    Parser.inState = False
    Parser.end = ''
    Parser.buffer = ''
    Parser.prefix = ''
    Parser.mode = None

    if mode == 'block' and prefix.strip() == '' and after.strip() == '':
      return [converted]

    text = prefix + converted + after
    had_conversion = True

  out = ''
  current = text
  changed = False

  while True:
    best = None
    for start, end, mode in tokens:
      idx = current.find(start)
      if idx == -1:
        continue
      if best is None or idx < best[0]:
        best = (idx, start, end, mode)

    if best is None:
      out += current
      break

    idx, start, end, mode = best
    out += current[:idx]
    rest = current[idx + len(start):]
    end_idx = rest.find(end)
    if end_idx == -1:
      Parser.inState = True
      Parser.end = end
      Parser.buffer = rest
      Parser.prefix = out
      Parser.mode = mode
      return res

    content = rest[:end_idx]
    after = rest[end_idx + len(end):]
    converted = converter.latex_to_text(content)

    if mode == 'block' and out.strip() == '' and after.strip() == '':
      return [converted]

    out += converted
    current = after
    changed = True

  if changed or had_conversion:
    return out
  return None
