#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "pygments",
#     "appdirs",
#     "toml",
# ]
# ///
import appdirs
import base64
import logging
import math
import os
import pty
import re
import select
import shutil
import sys
import tempfile
import termios
import toml
import traceback
from io import StringIO
import pygments.util
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import Terminal256Formatter
from pygments.styles import get_style_by_name
from pathlib import Path

default_toml = """
[features]
CodeSpaces = true
Clipboard = true
Logging = false
Margin = 2 
PrettyPad = false
Timeout = 0.5

[colors]
HSV = [320.0, 0.5, 0.5]
DARK =   { H = 1.00, S = 1.50, V = 0.30 }
MID  =   { H = 1.00, S = 1.00, V = 0.50 }
SYMBOL = { H = 1.00, S = 1.00, V = 1.50 }
HEAD =   { H = 1.00, S = 2.00, V = 1.50 }
BRIGHT = { H = 1.00, S = 2.00, V = 1.90 }
STYLE = "monokai"
"""

def ensure_config_file():
    config_dir = appdirs.user_config_dir("streamdown")
    os.makedirs(config_dir, exist_ok=True)
    config_path = Path(config_dir) / "config.toml"
    if not config_path.exists():
        config_path.write_text(default_toml)
    return config_path, config_path.read_text()

config_toml_path, config_toml_content = ensure_config_file()
config = toml.loads(config_toml_content)
colors = config.get("colors", {})
features = config.get("features", {})

# TODO
# we should have a "wait_for_newline" with a global handler of
# an accumulating line

# the ranges here are (float) [0-360, 0-1, 0-1]
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

H = colors.get("HSV")[0]
S = colors.get("HSV")[1]
V = colors.get("HSV")[2]

try:
    env_sd_colors = os.getenv("SD_BASEHSV")
    if env_sd_colors:
        env_colors = env_sd_colors.split(",")
        if len(env_colors) > 0: H = float(env_colors[0])
        if len(env_colors) > 1: S = float(env_colors[1])
        if len(env_colors) > 2: V = float(env_colors[2])
except Exception as e:
    logging.warning(f"Error parsing SD_BASEHSV: {e}")

def apply_multipliers(name, H, S, V):
    m = colors.get(name)
    return hsv2rgb(H * m['H'], S * m["S"], V * m["V"])

DARK   = apply_multipliers("DARK", H, S, V)
MID    = apply_multipliers("MID", H, S, V)
SYMBOL = apply_multipliers("SYMBOL", H, S, V)
HEAD   = apply_multipliers("HEAD", H, S, V)
BRIGHT = apply_multipliers("BRIGHT", H, S, V)

STYLE  = colors.get("STYLE", "monokai")
MARGIN = features.get("Margin", 2) 
MARGIN_SPACES = " " * MARGIN

FG = "\033[38;2;"
BG = "\033[48;2;"
RESET = "\033[0m"
FGRESET = "\033[39m"
BGRESET = "\033[49m"

BOLD =      ["\033[1m", "\033[22m"]
UNDERLINE = ["\033[4m", "\033[24m"]
ITALIC    = ["\033[3m", "\033[23m"]

CODEBG = f"{BG}{DARK}"


LINK = f"{FG}{SYMBOL}{UNDERLINE[0]}"

ANSIESCAPE = r"\033(\[[0-9;]*[mK]|][0-9]*;;.*?\\|\\)"
KEYCODE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

DEBUG_FH = None
def debug_write(text):
    global DEBUG_FH
    if state.Logging:
        if not DEBUG_FH:
            DEBUG_FH = tempfile.NamedTemporaryFile(prefix="sd_debug", delete=False, encoding="utf-8", mode="w")
        assert isinstance(text, str)
        print(f"{text}", file=DEBUG_FH, end="")
        DEBUG_FH.flush()

visible = lambda x: re.sub(ANSIESCAPE, "", x)
visible_length = lambda x: len(visible(x))
extract_ansi_codes = lambda text: re.findall(r"\033\[[0-9;]*[mK]", text)

_master, _slave = pty.openpty()  # Create a new pseudoterminal

def get_terminal_width():
    try:
        return shutil.get_terminal_size().columns
    except (AttributeError, OSError):
        return 80

FULLWIDTH = int(get_terminal_width())
WIDTH = FULLWIDTH - 2 * MARGIN
CODEPAD = [
    f"{RESET}{FG}{DARK}{'▄' * FULLWIDTH}{RESET}\n",
    f"{RESET}{FG}{DARK}{'▀' * FULLWIDTH}{RESET}"
]

class Goto(Exception):
    pass

class Code:
    Spaces = 'spaces'
    Backtick = 'backtick'
    Header = 'header'
    Body = 'body'

class ParseState:
    def __init__(self):

        self.buffer = ''
        self.first_line = True
        self.last_line_empty = False
        self.is_pipe = False
        self.is_pty = False
        self.maybe_prompt = False

        self.CodeSpaces = features.get("CodeSpaces", True)
        self.Clipboard = features.get("Clipboard", True)
        self.Logging = features.get("Logging", False)
        self.PrettyPad = features.get("PrettyPad", False)
        self.Timeout = features.get("Timeout", 0.5)

        # If the entire block is indented this will
        # tell us what that is
        self.first_indent = None
        self.has_newline = False

        # These are part of a trick to get
        # streaming code blocks while preserving
        # multiline parsing.
        self.code_buffer = ""
        self.code_gen = 0
        self.code_language = None
        self.code_first_line = False
        self.code_indent = 0
        self.code_line = ''

        self.ordered_list_numbers = []
        self.list_item_stack = []  # stack of (indent, type)

        self.bg = BGRESET    
        self.current_line = ''

        # So this can either be False, Code.Backtick or Code.Spaces
        self.in_list = False
        self.in_code = False
        self.in_bold = False
        self.in_italic = False
        self.in_table = False
        self.in_underline = False

        self.exit = 0

    def current(self):
        state = {
                # 'list': self.in_list,
                'code': self.in_code,
                'bold': self.in_bold,
                'italic': self.in_italic,
                'underline': self.in_underline
                }

        state['none'] = all(item is False for item in state.values())
        return state

    def space_left(self):
        if len(self.current_line) == 0:
            return MARGIN_SPACES
        return ""

    def reset_buffer(self):
        self.buffer = ''

state = ParseState()

def format_table(rowList):
    if not rowList: return []

    num_cols = len(rowList)
    if num_cols == 0: return []

    # Calculate max width per column (integer division)
    # Subtract num_cols + 1 for the vertical borders '│'
    available_width = WIDTH - (num_cols + 1)
    if available_width <= 0:
        # Handle extremely narrow terminals gracefully
        col_width = 1
    else:
        col_width = available_width // num_cols

    state.bg = f"{BG}{DARK}"

    # --- First Pass: Wrap text and calculate row heights ---
    row_height = 0
    wrapped_cellList = []
    for row in rowList:
        wrapped_cell = wrap_text(line_format(row), width=col_width)

        # Ensure at least one line, even for empty cells
        if not wrapped_cell:
            wrapped_cell = [""]

        wrapped_cellList.append(wrapped_cell)
        row_height = max(row_height, len(wrapped_cell))


    formatted = []

    # --- Second Pass: Format and emit rows ---
    bg_color = MID if state.in_table == Code.Header else DARK
    for ix in range(row_height):
        # This is the fancy row separator
        extra = f"\033[4;58;2;{MID}" if not state.in_table == Code.Header and (ix == row_height - 1) else ""
        line_segments = []

        # Now we want to snatch this row index from all our cells
        for cell in wrapped_cellList:
            segment = ''
            if ix < len(cell):
                segment = cell[ix]

            # Margin logic is correctly indented here
            margin_needed = col_width - visible_length(segment)
            margin_segment = segment + (" " * max(0, margin_needed))
            line_segments.append(f"{BG}{bg_color}{extra} {margin_segment}")

        # Correct indentation: This should be outside the c_idx loop
        joined_line = f"{BG}{bg_color}{extra}{FG}{SYMBOL}│{RESET}".join(line_segments)
        # Correct indentation and add missing characters
        formatted.append(f"{joined_line}{RESET}")
    state.bg = BGRESET
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

def wrap_text(text, width = WIDTH, indent = 0, first_line_prefix="", subsequent_line_prefix="", buffer=True):
    # Wraps text to the given width, preserving ANSI escape codes across lines.
    words = line_format(text).split()
    lines = []
    current_line = ""
    current_style = ""

    #if not buffer and visible_length(text) < WIDTH:
    #    return [text]
    
    for i, word in enumerate(words):
        # Accumulate ANSI codes within the current word
        codes = extract_ansi_codes(word)
        if codes:
            current_style += "".join(codes)

        if visible_length(current_line) + visible_length(word) + 1 <= width:  # +1 for space
            current_line += (" " if current_line else "") + word
        else:
            # Word doesn't fit, finalize the previous line
            prefix = first_line_prefix if not lines else subsequent_line_prefix
            line_content = prefix + current_line
            margin = width - visible_length(line_content)
            lines.append(line_content + (' ' * max(0, margin)) + RESET)

            # Start new line
            current_line = (" " * indent) + current_style + word

    # Add the last line
    if current_line:
        prefix = first_line_prefix if not lines else subsequent_line_prefix
        line_content = prefix + current_line
        margin = width - visible_length(line_content)
        lines.append(line_content + (' ' * max(0, margin)) + RESET)

    # Re-apply current style to the beginning of each subsequent line
    final_lines = []
    for i, line in enumerate(lines):
        if i == 0:
            final_lines.append(line)
        else:
            # Prepend the accumulated style. Since margin/RESET are already added,
            # this style applies to the *start* of the next logical text block.
            final_lines.append(current_style + line)

    return final_lines

def line_format(line):
    def not_text(token):
        return not token or len(token.rstrip()) != len(token)

    # Apply OSC 8 hyperlink formatting after other formatting
    def process_links(match):
        description = match.group(1)
        url = match.group(2)
        return f'\033]8;;{url}\033\\{LINK}{description}{UNDERLINE[1]}\033]8;;\033\\'

    line = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", process_links, line)
    tokenList = re.findall(r"(\*\*|\*|_|`|[^_*`]+)", line)
    result = ""
    last_token = None

    for token in tokenList:
        if token == "**" and (state.in_bold or not_text(last_token)):
            state.in_bold = not state.in_bold
            if state.in_code:
                result += token
            else:
                result += BOLD[0] if state.in_bold else BOLD[1]

        elif token == "*" and (state.in_italic or not_text(last_token)):
            state.in_italic = not state.in_italic
            if state.in_code:
                result += token
            else:
                result += ITALIC[0] if state.in_italic else ITALIC[1]

        elif token == "_" and (state.in_underline or not_text(last_token)):
            state.in_underline = not state.in_underline
            if state.in_code:
                result += token
            else:
                result += UNDERLINE[0] if state.in_underline else UNDERLINE[1]

        elif token == "`":
            state.in_code = not state.in_code
            if state.in_code:
                result += f'{BG}{MID}'
            else:
                result += state.bg
        else:
            result += token  

        last_token = token
    return result

# new strategy. We are going to call things need_newline and some thing not.
def parse(stream):
    last_line_empty_cache = None
    char = None
    process_buffer = False

    try:
        while True:
            if state.is_pty:
                ready, _, _ = select.select([stream.fileno(), _master], [], [], state.Timeout)

                if _master in ready:  # Read from PTY
                    data = os.read(_master, 1024)
                    if not data: break
                    clean_data = KEYCODE_RE.sub('', data.decode('utf-8'))
                    os.write(sys.stdout.fileno(), clean_data.encode())  # Write to stdout

                char = b''
                if stream.fileno() in ready:  # Read from stdin
                    while True:
                        char += os.read(stream.fileno(), 1)

                        # If this doesn't work then we are on a multi-byte
                        # and should be read in many of them
                        try:
                            char.decode('utf-8')
                            break
                        except:
                            continue

                    # This means end of input
                    if char == b'': break

                else:
                    # here I want to say there's nothing more we can add
                    # right this second and we should process the line
                    if len(state.buffer):
                        process_buffer = True

            else:
                char = stream.read(1)
                if len(char) == 0: break
                char = char.encode('utf-8')

            if char:
                state.buffer += char.decode('utf-8')

            debug_write(char.decode('utf-8'))
            if char != b'\n' and not process_buffer : continue

            #print(f"({char}-{bytes(state.buffer, 'utf-8')})")
            state.has_newline = state.buffer.endswith('\n')
            process_buffer = False

            state.maybe_prompt = not state.has_newline and state.current()['none'] and re.match('^.*>', state.buffer)
            #print(state.has_newline, state.current(), re.match('^.*>', state.buffer))

            # let's wait for a newline
            if state.maybe_prompt:
                yield state.buffer
                state.reset_buffer()
                continue

            if not state.has_newline:
                continue

            # Process complete line
            line = state.buffer
            state.reset_buffer()
            

            # --- Collapse Multiple Empty Lines if not in code blocks ---
            if not state.in_code:
                is_empty = line.strip() == ""

                if is_empty and state.last_line_empty:
                    continue  # Skip processing this line
                elif is_empty:
                    state.last_line_empty = True
                    yield ""
                    continue
                else:
                    last_line_empty_cache = state.last_line_empty
                    state.last_line_empty = False

            # This is to reset our top-level line-based systems
            # \n buffer
            if not state.in_list and len(state.ordered_list_numbers) > 0:
                state.ordered_list_numbers[0] = 0
            else:
                state.in_list = False

            if state.first_indent == None:
                state.first_indent = len(line) - len(line.lstrip())
            if len(line) - len(line.lstrip()) >= state.first_indent:
                line = line[state.first_indent:]
            else:
                logging.warning("Indentation decreased from first line.")


            # Indent guaranteed

            # in order to stream tables and keep track of the headers we need to know whether
            # we are in table or not table otherwise > 1 tables won't have a stylized header
            if state.in_table and not state.in_code and not re.match(r"^\s*\|.+\|\s*$", line):
                state.in_table = False

            #
            # <code><pre>
            #
            # This needs to be first
            if not state.in_code:
                code_match = re.match(r"\s*```\s*([^\s]+|$)", line)
                if code_match:
                    state.in_code = Code.Backtick
                    state.code_language = code_match.group(1) or 'Bash'

                elif state.CodeSpaces and last_line_empty_cache and not state.in_list:
                    code_match = re.match(r"^    ", line)
                    if code_match:
                        state.in_code = Code.Spaces
                        state.code_language = 'Bash'

                if state.in_code:
                    state.code_buffer = ""
                    state.code_gen = 0
                    state.code_first_line = True
                    state.bg = f"{BG}{DARK}"
                    if state.PrettyPad:
                        yield CODEPAD[0]
                    else:
                        yield "\n"

                    logging.debug(f"In code: ({state.in_code})")

                    if state.in_code == Code.Backtick:
                        continue

            if state.in_code:
                try:
                    if not state.code_first_line and (
                            (state.in_code == Code.Backtick and     line.strip() == "```") or
                            (state.CodeSpaces and state.in_code == Code.Spaces   and not line.startswith('    '))
                        ):
                        state.code_language = None
                        state.code_indent = 0
                        code_type = state.in_code
                        state.in_code = False
                        state.bg = BGRESET

                        if state.PrettyPad:
                            yield CODEPAD[1]
                        else:
                            yield f"{RESET}\n"

                        logging.debug(f"Not in code: {state.in_code}")

                        if code_type == Code.Backtick:
                            continue
                        else:
                            # otherwise we don't want to consume
                            # nor do we want to be here.
                            raise Goto()

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
                    
                    state.code_line += line
                    if state.code_line.endswith('\n'):
                        line = state.code_line
                        state.code_line = ''
                    else:
                        continue

                    indent, line_wrap = code_wrap(line)
      
                    for tline in line_wrap:
                        # wrap-around is a bunch of tricks. We essentially format longer and longer portions of code. The problem is
                        # the length can change based on look-ahead context so we need to use our expected place (state.code_gen) and
                        # then naively search back until our visible_lengths() match. This is not fast and there's certainly smarter
                        # ways of doing it but this thing is way trickery than you think
                        highlighted_code = highlight(state.code_buffer + tline, lexer, formatter)
        
                        # Since we are streaming we ignore the resets and newlines at the end
                        if highlighted_code.endswith(FGRESET + "\n"):
                            highlighted_code = highlighted_code[: -(1 + len(FGRESET))]

                        # turns out highlight will eat leading newlines on empty lines
                        vislen = visible_length(state.code_buffer.lstrip())

                        delta = 0
                        while visible_length(highlighted_code[:(state.code_gen-delta)]) > vislen:
                            delta += 1

                        state.code_buffer += tline

                        this_batch = highlighted_code[state.code_gen-delta :]
                        if this_batch.startswith(FGRESET):
                            this_batch = this_batch[len(FGRESET) :]

                        logging.debug(f"{state.code_buffer} {bytes(this_batch, 'utf-8')}")

                        ## this is the crucial counter that will determine
                        # the begninning of the next line
                        state.code_gen = len(highlighted_code)

                        code_line = ' ' * indent + this_batch.strip()
                        #print(f"--{code_line}--")

                        margin = FULLWIDTH - visible_length(code_line)
                        yield f"{CODEBG}{code_line}{' ' * max(0, margin)}{BGRESET}"  
                    continue
                except Goto as ex:
                    pass
                
                except Exception as ex:
                    logging.warning(f"Code parsing error: {ex}")
                    traceback.print_exc()
                    pass

            #
            # <table>
            #
            if re.match(r"^\s*\|.+\|\s*$", line) and not state.in_code:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]

                # This guarantees we are at the first line
                # \n buffer
                if not state.in_table:
                    state.in_table = Code.Header

                    # This should come at line 2
                elif state.in_table == Code.Header:
                    # we ignore the separator, this is just a check
                    if not re.match(r"^[\s|:-]+$", line):
                        logging.warning(f"Table definition row 2 was NOT a separator. Instead it was:\n({line})")

                    # Let's assume everything worked out I guess.
                    # We set our header to false and basically say
                    # we are expecting the body
                    state.in_table = Code.Body 
                    # And then ignore this row since we ignore the separator
                    continue


                formatted = format_table(cells)
                for l in formatted:
                    yield f"{MARGIN_SPACES}{l}"

                continue

            #
            # <li> <ul> <ol>
            #
            list_item_match = re.match(r"^(\s*)([*\-]|\d+\.)\s+(.*)", line)
            if list_item_match:
                state.in_list = True
                indent = len(list_item_match.group(1))
                list_type = "number" if list_item_match.group(2)[0].isdigit() else "bullet"
                content = list_item_match.group(3)

                # Handle stack
                while state.list_item_stack and state.list_item_stack[-1][0] > indent:
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
                    state.ordered_list_numbers[-1] += 1

                indent = len(state.list_item_stack) * 2

                wrap_width = WIDTH - indent - 4

                if list_type == "number":
                    list_number = int(max(state.ordered_list_numbers[-1], float(list_item_match.group(2))))
                    bullet = f"{list_number}"
                    first_line_prefix = f"{(' ' * (indent - len(bullet)))}{FG}{SYMBOL}{bullet}{RESET} "
                    subsequent_line_prefix = " " * (indent-1)
                else:
                    first_line_prefix = " " * (indent - 1) + f"{FG}{SYMBOL}•{RESET}" + " "
                    subsequent_line_prefix = " " * (indent-1)

                wrapped_lineList = wrap_text(
                    content,
                    wrap_width, 2,
                    first_line_prefix,
                    subsequent_line_prefix,
                    buffer = False
                )
                for wrapped_line in wrapped_lineList:
                    yield f"{state.space_left()}{wrapped_line}\n"
                continue
            #
            # <hr>
            #
            if re.match(r"^[\s]*[-*_]{3,}[\s]*$", line):
                # print a horizontal rule using a unicode midline 
                yield f"{MARGIN_SPACES}{FG}{SYMBOL}{'─' * WIDTH}{RESET}"
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
                if level == 1:      # #
                    yield f"\n{MARGIN_SPACES}{BOLD[0]}{' ' * math.floor(spaces_to_center)}{text}{' ' * math.ceil(spaces_to_center)}{BOLD[1]}\n"
                elif level == 2:    # ##
                    yield f"\n{MARGIN_SPACES}{BOLD[0]}{FG}{BRIGHT}{' ' * math.floor(spaces_to_center)}{text}{' ' * math.ceil(spaces_to_center)}{RESET}\n\n"
                elif level == 3:    # ###
                    yield f"\n{MARGIN_SPACES}{FG}{HEAD}{BOLD[0]}{text}{RESET}"
                elif level == 4:    # ####
                    yield f"{MARGIN_SPACES}{FG}{SYMBOL}{text}{RESET}"
                elif level == 5:    # #####
                    yield f"{MARGIN_SPACES}{text}{RESET}"
                else:  # level == 6
                    yield f"{MARGIN_SPACES}{text}{RESET}"
                continue

            if len(line) == 0: print("")
            if len(line) < WIDTH:
                # we want to prevent word wrap
                yield f"{state.space_left()}{line_format(line)}"
            else:
                wrapped_lines = wrap_text(line)
                # print(f"({line})")
                for wrapped_line in wrapped_lines:
                    yield f"{state.space_left()}{wrapped_line}\n"

    except Exception as e:
        logging.error(f"Parser error: {str(e)}")
        traceback.print_exc()
        raise

def main():
    logging.basicConfig(stream=sys.stdout,
        level=os.getenv('LOGLEVEL') or logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        inp = sys.stdin
        if len(sys.argv) > 1:
            try:
                inp = open(sys.argv[1], "r")
            except FileNotFoundError:
                logging.error(f"Error: File not found: {sys.argv[1]}")
        elif sys.stdin.isatty():
            print(f"SD_BASEHSV: {H}, {S}, {V}\nPalette: ", end=" ")
            for (a,b) in (("DARK", DARK), ("MID", MID), ("SYMBOL", SYMBOL), ("BRIGHT", BRIGHT)):
                print(f"{FG}{b}{a}{RESET} {BG}{b}{a}{RESET}", end=" | ")
            print(f"\nConfig: {config_toml_path}\n")

            # This isn't what injecting into a clipboard is for
            state.Clipboard = False

            inp = StringIO("""
                 **A markdown renderer for modern terminals**
                 ##### Usage examples:

                 ``` bash
                 sd [filename]
                 cat README.md | sd
                 stdbuf -oL llm chat | sd
                 SD_BASEHSV=100,0.4,0.8 sd <(curl -s https://raw.githubusercontent.com/kristopolous/Streamdown/refs/heads/main/tests/fizzbuzz.md)
                 ```

                 If no filename is provided and no input is piped, this help message is displayed.

                 """)
        else:
            # this is a more sophisticated thing that we'll do in the main loop
            state.is_pty = True
            os.set_blocking(inp.fileno(), False) 

        for chunk in parse(inp):
            if not state.has_newline:
                chunk = chunk.rstrip("\n")
            elif not chunk.endswith("\n"):
                chunk += "\n"

            if chunk.endswith("\n"):
                state.current_line = ''
            else:
                state.current_line += chunk
                
            if state.is_pty:
                print(chunk, end="", flush=True)
                #os.write(_slave, bytes(chunk, 'utf-8'))  # Write to PTY
            else:
                sys.stdout.write(chunk)
            sys.stdout.flush()

    except KeyboardInterrupt:
        state.exit = 130
        
    except Exception as ex:
        logging.warning(f"Exception thrown: {ex}")

    if state.Clipboard and state.code_buffer:
        code = state.code_buffer
        # code needs to be a base64 encoded string before emitting
        code_bytes = code.encode('utf-8')
        base64_bytes = base64.b64encode(code_bytes)
        base64_string = base64_bytes.decode('utf-8')
        print(f"\033]52;c;{base64_string}\a", end="", flush=True)

    sys.exit(state.exit)
if __name__ == "__main__":
    main()
