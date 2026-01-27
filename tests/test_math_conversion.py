import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from streamdown.plugins import latex


def reset_parser():
    latex.Parser.mode = None
    latex.Parser.end = ""
    latex.Parser.buffer = ""
    latex.Parser.prefix = ""


def run_lines(lines):
    output = []
    in_code = False

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_code = not in_code
            output.append(line)
            continue

        if in_code:
            output.append(line)
            continue

        res = latex.Plugin(line)
        if res is True:
            continue
        if isinstance(res, str):
            output.append(res)
        elif res is not None:
            output.extend(res)
        else:
            output.append(line)

    return output


class MathConversionTests(unittest.TestCase):
    def setUp(self):
        reset_parser()

    def test_inline_parens(self):
        text = "".join(run_lines(["Inline \\(a+b\\) test.\n"]))
        self.assertIn("a+b", text)
        self.assertNotIn("\\(", text)
        self.assertNotIn("\\)", text)

    def test_multiple_inline_segments(self):
        text = "".join(run_lines(["Mix \\(a\\) and \\(b\\).\n"]))
        self.assertIn("a", text)
        self.assertIn("b", text)
        self.assertNotIn("\\(", text)
        self.assertNotIn("\\)", text)

    def test_block_brackets_multiline(self):
        text = "".join(run_lines(["\\[\n", "a^2 + b^2\n", "\\]\n"]))
        self.assertIn("a^2 + b^2", text)
        self.assertNotIn("\\[", text)
        self.assertNotIn("\\]", text)

    def test_block_dollars_same_line(self):
        text = "".join(run_lines(["$$ a+b $$\n"]))
        self.assertIn("a+b", text)
        self.assertNotIn("$$", text)

    def test_multiple_blocks_same_line(self):
        text = "".join(run_lines(["Eq $$a$$ and $$b$$.\n"]))
        self.assertIn("a", text)
        self.assertIn("b", text)
        self.assertNotIn("$$", text)

    def test_inline_with_block_markers(self):
        text = "".join(run_lines(["Text $$a$$ more.\n"]))
        self.assertIn("Text", text)
        self.assertIn("a", text)
        self.assertIn("more", text)
        self.assertNotIn("$$", text)

    def test_streamed_inline_across_lines(self):
        text = "".join(run_lines(["Before \\(a\n", "b\\) after.\n"]))
        self.assertIn("Before", text)
        compact = "".join(text.split())
        self.assertIn("ab", compact)
        self.assertIn("after", text)
        self.assertNotIn("\\(", text)
        self.assertNotIn("\\)", text)

    def test_unclosed_inline_buffers(self):
        output = run_lines(["Start \\(a+b\n"])
        self.assertEqual(output, [])

    def test_non_math_line_unchanged(self):
        text = "".join(run_lines(["No math here.\n"]))
        self.assertEqual(text, "No math here.\n")

    def test_code_block_skips_conversion(self):
        text = "".join(
            run_lines(
                [
                    "```python\n",
                    "x = \"\\\\(a+b\\\\)\"\n",
                    "```\n",
                ]
            )
        )
        self.assertIn("\\\\(", text)
        self.assertIn("\\\\)", text)


if __name__ == "__main__":
    unittest.main()
