#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "pygments",
# ]
# ///
import sys
import re
import shutil
from io import StringIO
import pygments.util
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import Terminal256Formatter
from pygments.styles import get_style_by_name
import math
import os
import logging
import tempfile

# the ranges here are 0-360, 0-1, 0-1
def hsv2rgb(h, s, v):
    s = min(1, s)
    v = min(1, v)
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    # scale this to 0-255 and return it in R;G;Bm format

    return ';'.join([str(x) for x in [
        min(255,int((r + m) * 255)), 
        min(255,int((g + m) * 255)), 
        min(255,int((b + m) * 255))
    ]]) + "m"
            
# Coloring starts with a base HSV, which can be overridden
# by the SD_COLORS environment variable.
H = 320
S = 0.5
V = 0.5

try:
    sd_colors = os.getenv("SD_BASEHSV")
    if sd_colors:
        colors = sd_colors.split(",")
        if len(colors) > 0:
            H = float(colors[0])
        if len(colors) > 1:
            S = float(colors[1])
        if len(colors) > 2:
            V = float(colors[2])
except Exception as e:
    logging.warn(f"Error parsing SD_BASEHSV: {e}")

# Then we have a few theme variations based
# on multipliers
DARK   = hsv2rgb(H, S * 1.50, V * 0.30)
MID    = hsv2rgb(H, S       , V * 0.50)
BRIGHT = hsv2rgb(H, S * 2.00, V       )
SYMBOL = hsv2rgb(H, S       , V * 1.50) 
STYLE  = "monokai"
# And that is all.

INDENT = 2
INDENT_SPACES = " " * INDENT

FG = "\033[38;2;"
BG = "\033[48;2;"
RESET = "\033[0m"
FGRESET = "\033[39m"
BGRESET = "\033[49m"

def get_terminal_width():
    try:
        return shutil.get_terminal_size().columns
    except (AttributeError, OSError):
        # Fallback to 80 columns
        return 80

FULLWIDTH = int(get_terminal_width())
WIDTH = FULLWIDTH - 2 * INDENT

BOLD =      ["\033[1m", "\033[22m"]
UNDERLINE = ["\033[4m", "\033[24m"]
ITALIC    = ["\033[3m", "\033[23m"]

CODEBG = f"{BG}{DARK}"
CODEPAD = f"{RESET}{CODEBG}{' ' * FULLWIDTH}{RESET}\n"

LINK= f"{FG}{SYMBOL}{UNDERLINE[0]}"

ANSIESCAPE = r"\033(\[[0-9;]*[mK]|][0-9]*;;.*?\\|\\)"

DEBUG_FH = None
def debug_write(text):
    global DEBUG_FH
    if SD_DEBUG:
        if not DEBUG_FH:
            DEBUG_FH = tempfile.NamedTemporaryFile(prefix="sd_debug", delete=False, encoding="utf-8", mode="w")
        assert isinstance(text, str)
        print(text, file=DEBUG_FH)
        DEBUG_FH.flush()
        
SD_DEBUG = os.getenv("SD_DEBUG") or False


visible = lambda x: re.sub(ANSIESCAPE, "", x)
visible_length = lambda x: len(visible(x)) 


def extract_ansi_codes(text):
    """Extracts all ANSI escape codes from a string."""
    return re.findall(r"\033\[[0-9;]*[mK]", text)


class TableState:
    def __init__(self):
        self.rows = []
        self.in_header = False
        self.in_separator = False
        self.in_body = False

    def reset(self):
        self.__init__()

    def intable(self):
        return self.in_header or self.in_separator or self.in_body


class ParseState:
    def __init__(self):
        # So this can either be False, "backtick" or "spaces"
        self.in_code = False

        self.table = TableState()
        self.buffer = []
        self.list_item_stack = []  # stack of (indent, type)
        self.first_line = True
        self.last_line_empty = False

        # These are part of a trick to get
        # streaming code blocks while preserving
        # multiline parsing.
        self.code_buffer = []
        self.code_gen = 0
        self.code_language = None
        self.code_first_line = False
        self.code_indent = 0
        self.ordered_list_numbers = []
        self.in_list = False

    def isempty(self):
        return self.in_code
    
    def debug(self):
        """print out every variable in ParseState and TableState"""
        for key, value in self.__dict__.items():
            logging.debug(f"{key:20}: {value}")
        for key, value in self.table.__dict__.items():
            logging.debug(f"table.{key:20}: {value}")

    def reset_buffer(self):
        self.buffer = []


def format_table(table_rows):
    """Formats markdown tables with unicode borders and alternating row colors"""
    if not table_rows:
        return []

    # Extract headers and rows, skipping separator
    headers = [cell.strip() for cell in table_rows[0]]
    rows = [
        [cell.strip() for cell in row]
        for row in table_rows[1:]
        if not re.match(r"^[\s|:-]+$", "|".join(row))
    ]

    # Calculate column widths
    col_widths = [
        max(len(str(item)) for item in col) + 2  # +2 for padding
        for col in zip(headers, *rows)
    ]

    formatted = []

    # Header row
    header_cells = [
        f"{BOLD[0]} {header.ljust(width)} {BOLD[1]}"
        for header, width in zip(headers, col_widths)
    ]
    header_line = "│".join(header_cells)
    formatted.append(f" {BG}{MID}{header_line}{RESET}")

    # Data rows
    for i, row in enumerate(rows):
        color = 236 if i % 2 == 0 else 238
        row_cells = [f" {cell.ljust(width)} " for cell, width in zip(row, col_widths)]
        row_line = "│".join(row_cells)
        formatted.append(f" {BG}{DARK}{row_line}{RESET}")
    return formatted

def code_wrap(text_in):
    # get the indentation of the first line
    indent = len(text_in) - len(text_in.lstrip())
    text = text_in.lstrip()
    mywidth = FULLWIDTH - indent

    # We take special care to preserve empty lines
    if len(text) == 0:
        return (0, [text_in])
    res = [text[:mywidth]]

    for i in range(mywidth, len(text), mywidth):
        res.append(text[i : i + mywidth]) 
    
    return (indent, res)

def wrap_text(text, width = WIDTH, indent = 0, first_line_prefix="", subsequent_line_prefix=""):
    # Wraps text to the given width, preserving ANSI escape codes across lines.
    words = line_format(text).split()
    lines = []
    current_line = ""
    current_style = ""

    for i, word in enumerate(words):
        # Accumulate ANSI codes within the current word
        codes = extract_ansi_codes(word)
        if codes:
            current_style += "".join(codes)

        if visible_length(current_line) + visible_length(word) + 1 <= width:  # +1 for space
            current_line += (" " if current_line else "") + word
        else:
            # Close previous line with reset and then re-apply current style
            if not lines:  # First line
                lines.append(first_line_prefix + current_line + RESET)
            else:
                lines.append(subsequent_line_prefix + current_line + RESET)

            # Reset current line and apply the preserved style
            current_line = (" " * indent) + current_style + word

    if current_line:
        if not lines:  # only one line
            lines.append(first_line_prefix + current_line + RESET)
        else:
            lines.append(subsequent_line_prefix + current_line + RESET)

    # Re-apply current style to the beginning of each line (except the first)
    final_lines = []
    for i, line in enumerate(lines):
        if i == 0:
            final_lines.append(line)
        else:
            final_lines.append(current_style + line)

    return final_lines

def line_format(line):
    def not_text(token):
        return not token or len(token.rstrip()) != len(token)

    # Apply OSC 8 hyperlink formatting after other formatting
    def process_links(match):
        description = match.group(1)
        url = match.group(2)
        return f'\033]8;;{url}\033\\{LINK}{description}{RESET}\033]8;;\033\\'
    
    line = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", process_links, line)
    
    tokens = re.findall(r"(\*\*|\*|_|`|[^_*`]+)", line)
    in_bold = False
    in_italic = False
    in_underline = False
    in_code = False
    result = ""
    last_token = None

    for token in tokens:
        if token == "**" and (in_bold or not_text(last_token)):
            in_bold = not in_bold
            if not in_code:
                result += BOLD[0] if in_bold else BOLD[1]
            else:
                result += token  # Output the delimiter inside code
        elif token == "*" and (in_italic or not_text(last_token)):
            in_italic = not in_italic
            if not in_code:
                result += ITALIC[0] if in_italic else ITALIC[1]
            else:
                result += token
        elif token == "_" and (in_underline or not_text(last_token)):
            in_underline = not in_underline
            if not in_code:
                result += UNDERLINE[0] if in_underline else UNDERLINE[1]
            else:
                result += token
        elif token == "`":
            in_code = not in_code
            if in_code:
                result += f"{BG}{MID}"  
            else:
                result += RESET 
        else:
            result += token  # Always output text tokens

        last_token = token
    return result

def parse(input_source):
    if isinstance(input_source, str):
        stdin = StringIO(input_source)
    else:
        stdin = input_source

    state = ParseState()
    try:
        while True:
            char = stdin.read(1)
            if not char: 
              if len(state.buffer):
                char = "\n"
              else:
                break

            state.buffer.append(char)

            if char != "\n": continue

            # Process complete line
            line = "".join(state.buffer).rstrip("\n")
            state.reset_buffer()
            debug_write(line)

            # --- Collapse Multiple Empty Lines if not in code blocks ---
            if not state.in_code:
                is_empty = line.strip() == ""

                if is_empty and state.last_line_empty:
                    continue  # Skip processing this line
                elif is_empty:
                    state.last_line_empty = True
                    yield "\n"
                    continue
                else:
                    state.last_line_empty = False

            # This is to reset our top-level list counter.
            if not state.in_list and len(state.ordered_list_numbers) > 0:
                state.ordered_list_numbers[0] = 0
            else:
                state.in_list = False


            # This order is important because the 4 space version of the code
            # isn't a consumed formatting line.
            code_match = re.match(r"(^    |\s*```)\s*([^\s]+|$)", line)
            logging.debug(code_match)

            if not state.in_code and code_match and ((state.last_line_empty and code_match.group(1) == '    ' and not state.in_list) or code_match.group(1).endswith('```')):

                logging.debug("In code")
                state.code_buffer = []
                state.code_gen = 0
                state.code_first_line = True

                yield CODEPAD

                # spaced version doesn't have language specification ability
                state.in_code = 'spaces'
                state.code_language = 'Bash'

                if code_match.group(1) == '```':
                    state.code_language = code_match.group(2) or 'Bash'
                    state.in_code = 'backtick'
                    continue
            #
            # <code><pre>
            #
            if state.in_code:
                if not state.code_first_line and (line.strip() == "```" or (state.in_code == 'spaces' and not line.startswith('    '))):     
                    logging.debug("Not in code")
                    state.code_language = None
                    state.code_indent = 0
                    yield CODEPAD
                    code_type = state.in_code 
                    state.in_code = False
                    if code_type == 'backtick':
                        continue
                    # otherwise we don't want to consume

                if state.code_first_line:
                    state.code_first_line = False
                    try:
                        lexer = get_lexer_by_name(state.code_language)
                        custom_style = get_style_by_name(STYLE)
                    except pygments.util.ClassNotFound:
                        lexer = get_lexer_by_name("Bash")
                        custom_style = get_style_by_name("default")

                    formatter = Terminal256Formatter(style=custom_style)
                    for i, char in enumerate(line):
                        if char == " ":
                            state.code_indent += 1
                        else:
                            break
                    line = line[state.code_indent :]

                elif line.startswith(" " * state.code_indent):
                    line = line[state.code_indent :]

                # By now we have the properly stripped code line
                # in the line variable. Add it to the buffer.
                indent, line_wrap = code_wrap(line)
                state.code_buffer.append('')

                for tline in line_wrap:
                    # wrap-around is a bunch of tricks. We essentially format longer and longer portions of code. The problem is 
                    # the length can change based on look-ahead context so we need to use our expected place (state.code_gen) and
                    # then naively search back until our visible_lengths() match. This is not fast and there's certainly smarter
                    # ways of doing it but this thing is way trickery than you think
                    highlighted_code = highlight("\n".join(state.code_buffer) + tline, lexer, formatter)


                    # Since we are streaming we ignore the resets and newlines at the end
                    if highlighted_code.endswith(FGRESET + "\n"):
                        highlighted_code = highlighted_code[: -(1 + len(FGRESET))]

                    # turns out highlight will eat leading newlines on empty lines
                    vislen = visible_length("\n".join(state.code_buffer).lstrip())

                    delta = 0
                    while visible_length(highlighted_code[:(state.code_gen-delta)]) > vislen:
                        delta += 1

                    state.code_buffer[-1] += tline

                    this_batch = highlighted_code[state.code_gen-delta :]
                    if this_batch.startswith(FGRESET):
                        this_batch = this_batch[len(FGRESET) :]

                    logging.debug(f"{state.code_buffer} {bytes(this_batch, 'utf-8')}")

                    ## this is the crucial counter that will determine
                    # the begninning of the next line
                    state.code_gen = len(highlighted_code)
                   
                    code_line = ' ' * indent + this_batch.strip() 
                    
                    padding = FULLWIDTH - visible_length(code_line)
                    yield f"{CODEBG}{code_line}{' ' * max(0, padding)}{BGRESET}\n"
                continue

          
            #
            # <table>
            #
            if re.match(r"^\s*\|.+\|\s*$", line) and not state.in_code:
                if not state.table.in_header and not state.table.in_body:
                    state.table.in_header = True

                cells = [c.strip() for c in line.strip().strip("|").split("|")]

                if state.table.in_header:
                    if re.match(r"^[\s|:-]+$", line):
                        state.table.in_header = False
                        state.table.in_separator = True
                    else:
                        state.table.rows.append(cells)
                elif state.table.in_separator:
                    state.table.in_separator = False
                    state.table.in_body = True
                    state.table.rows.append(cells)
                elif state.table.in_body:
                    state.table.rows.append(cells)

                if not state.table.intable():
                    yield f"{line}\n"
                continue
            else:
                if state.table.in_body or state.table.in_header:
                    formatted = format_table(state.table.rows)
                    for l in formatted:
                        yield f" {l}\n"
                    state.table.reset()

                #
                # <li> <ul> <ol>
                #
                list_item_match = re.match(r"^(\s*)([*\-]|\d+\.)\s+(.*)", line)
                if list_item_match:
                    state.in_list = True
                    indent = len(list_item_match.group(1))
                    list_type = (
                        "number" if list_item_match.group(2)[0].isdigit() else "bullet"
                    )
                    content = list_item_match.group(3)

                    # Handle stack
                    while (
                        state.list_item_stack and state.list_item_stack[-1][0] > indent
                    ):
                        state.list_item_stack.pop()  # Remove deeper nested items
                        if state.ordered_list_numbers:
                            state.ordered_list_numbers.pop()
                    if state.list_item_stack and state.list_item_stack[-1][0] < indent:
                        # new nested list
                        state.list_item_stack.append((indent, list_type))
                        state.ordered_list_numbers.append(0)
                    elif not state.list_item_stack:
                        # first list
                        state.list_item_stack.append((indent, list_type))
                        state.ordered_list_numbers.append(0)
                    if list_type == "number":
                        # print(json.dumps([indent, state.ordered_list_numbers]))
                        state.ordered_list_numbers[-1] += 1

                    indent = len(state.list_item_stack) * 2

                    wrap_width = WIDTH - indent - 4

                    if list_type == "number":
                        list_number = int(max(state.ordered_list_numbers[-1], float(list_item_match.group(2))))
                        bullet = f"{list_number}"
                        first_line_prefix = (
                            " " * (indent - len(bullet))
                            + f"{FG}{SYMBOL}{bullet}{RESET}"
                            + " "
                        )
                        subsequent_line_prefix = " " * (indent-1)
                    else:
                        first_line_prefix = ( " " * (indent - 1) + f"{FG}{SYMBOL}•{RESET}" + " ")
                        subsequent_line_prefix = " " * (indent-1)

                    wrapped_lines = wrap_text(
                        content,
                        wrap_width,
                        2,
                        first_line_prefix,
                        subsequent_line_prefix,
                    )
                    for wrapped_line in wrapped_lines:
                        yield f"{INDENT_SPACES}{wrapped_line}\n"
                    continue

                # 
                # <h1> <h2> <h3>
                # <h4> <h5> <h6>
                #
                header_match = re.match(r"^\s*(#{1,6})\s+(.*)", line)
                if header_match:
                    level = len(header_match.group(1))
                    text = header_match.group(2)
                    spaces_to_center = ((WIDTH - visible_length(text)) / 2)
                    if level == 1:
                        yield f"\n{INDENT_SPACES}{BOLD[0]}{' ' * math.floor(spaces_to_center)}{text}{' ' * math.ceil(spaces_to_center)}{BOLD[1]}\n\n"  
                    elif level == 2:
                        yield f"\n{INDENT_SPACES}{BOLD[0]}{FG}{BRIGHT}{' ' * math.floor(spaces_to_center)}{text}{' ' * math.ceil(spaces_to_center)}{RESET}\n\n"  
                    elif level == 3:
                        yield f"{INDENT_SPACES}{FG}{SYMBOL}  {FG}{BRIGHT}{text}{RESET}\n\n" 
                    elif level == 4:
                        yield f"{INDENT_SPACES}{FG}{SYMBOL}{text}{RESET}\n" 
                    elif level == 5:
                        yield f"{INDENT_SPACES}{text}{RESET}\n"  
                    else:  # level == 6
                        yield f"{INDENT_SPACES}{text}{RESET}\n"  

                else:
                    #
                    # <hr>
                    #
                    if re.match(r"^[\s]*[-*_]{3,}[\s]*$", line):
                        # print a horizontal rule using a unicode midline with a unicode fleur de lis in the middle
                        yield f"{INDENT_SPACES}{FG}{SYMBOL}{'─' * WIDTH}{RESET}\n"
                    else:
                        if len(line) == 0:
                            print("")
                        else:
                            # This is the basic unformatted text. We still want to word wrap it.
                            wrapped_lines = wrap_text(line)
                            for wrapped_line in wrapped_lines:
                                yield f"{INDENT_SPACES}{wrapped_line}\n" 

                # Process any remaining table data
                if state.table.rows:
                    formatted = format_table(state.table.rows)
                    for l in formatted:
                        yield f"{l}\n"
                    state.table.reset()

    except Exception as e:
        logging.error(f"Parser error: {str(e)}")
        raise

def main():
    logging.basicConfig(
        stream=sys.stdout,
        level=os.getenv('LOGLEVEL') or logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        inp = sys.stdin
        if len(sys.argv) > 1:
            try:
                inp = open(sys.argv[1], "r")
            except FileNotFoundError:
                logging.error(f"Error: File not found: {sys.argv[1]}")
        elif sys.stdin.isatty():
            print(f"Base HSV: {H}, {S}, {V} Palette: ", end=" ")
            for (a,b) in (("DARK", DARK), ("MID", MID), ("SYMBOL", SYMBOL), ("BRIGHT", BRIGHT)):
                print(f"{FG}{b}{a}{RESET} {BG}{b}{a}{RESET}", end=" | ")
            print("")

            inp = """
                 **A markdown renderer for modern terminals**
                 ##### Usage examples:

                 ``` bash
                 sd [filename]
                 cat README.md | sd
                 stdbuf -oL llm chat | sd 
                 ```

                 If no filename is provided and no input is piped, this help message is displayed.

                 """

        for chunk in parse(inp):
            sys.stdout.write(chunk)
            sys.stdout.flush()
    except KeyboardInterrupt:
        pass
if __name__ == "__main__":
    main()
