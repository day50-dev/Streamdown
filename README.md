# Streamdown

[![PyPI version](https://badge.fury.io/py/streamdown.svg)](https://badge.fury.io/py/streamdown)

I needed a streaming Markdown TUI CLI shell parser and honestly all the ones I found lacking. They were broken or janky in some kind of way. So here we go. From the ground up. It's a bad idea but it has to be done.

[sd demo](https://github.com/user-attachments/assets/48dba6fa-2282-4be9-8087-a2ad8e7c7d12)


This will work with [simonw's llm](https://github.com/simonw/llm) unlike with [richify.py](https://github.com/gianlucatruda/richify) which jumps around the page or blocks with an elipses or [glow](https://github.com/charmbracelet/glow) which buffers everything, this streams and does exactly what you want.

## Some Features

#### Provides clean copyable code for long code blocks and short terminals. 
![copyable](https://github.com/user-attachments/assets/7462c278-904c-4dbc-b09d-72254e7e639d)

#### Does OSC 8 links for modern terminals.

[links.webm](https://github.com/user-attachments/assets/a5f71791-7c58-4183-ad3b-309f470c08a3)


#### Doesn't consume characters like _ and * as style when they are in `blocks like this` because `_they_can_be_varaiables_`
![dunder](https://github.com/user-attachments/assets/eb9ab001-3bc7-4e4b-978f-bc00f29c2a41)

#### Also, tables are carefully supported to hopefully not be too broken
![table](https://github.com/user-attachments/assets/265509b1-d910-467a-ac39-f219c128e32d)


## Configuration
Streamdown uses a configuration file located at `~/.config/streamdown/config.toml` (following the XDG Base Directory Specification). If this file does not exist upon first run, it will be created with default values.

The configuration file uses TOML format and currently supports the following sections:

**`[colors]`**

This section defines the base Hue (H), Saturation (S), and Value (V) from which all other palette colors are derived. Due to limitations in TOML, these all must be floats (have a decimal point).

*   `HSV`: [ 0.0 - 360.0, 0.0 - 1.0, 0.0 - 1.0 ] 
*   `DARK`: Multipliers for background elements, code blocks. (Default: S=1.50, V=0.30)
*   `MID`: Multipliers for inline code backgrounds, table headers. (Default: S=1.00, V=0.50)
*   `SYMBOL`: Multipliers for list bullets, horizontal rules, links. (Default: S=1.00, V=1.50)
*   `HEAD`: Multipliers for level 3 headers. (Default: S=2.00, V=1.50)
*   `BRIGHT`: Multipliers for level 2 headers. (Default: S=2.00, V=1.90)

Example:
```toml
[colors]
HSV = [240.0, 0.5, 0.5]
DARK = { H = 1.0, S = 1.2, V = 0.25 } # Make dark elements less saturated and darker
SYMBOL = { H = 1.0, S = 1.8, V = 1.8 } # Make symbols more vibrant
```

The [highlighting themes come via pygments](https://pygments.org/styles/).

**`[features]`**

This section controls optional features:

*   `CodeSpaces` (boolean, default: `true`): Enables detection of code blocks indented with 4 spaces. Set to `false` to disable this detection method (triple-backtick blocks still work).
*   `Clipboard` (boolean, default: `true`): Enables copying the last code block encountered to the system clipboard using OSC 52 escape sequences upon exit. Set to `false` to disable.
*   `Margin` (integer, default: `2`): The left and right indent for the output. 
*   `PrettyPad` (boolean, default: `false`): Uses a unicode vertical pad trick to add a half height background to code blocks. This makes copy/paste have artifacts. See [#2](https://github.com/kristopolous/Streamdown/issues/2). I like it on. But that's just me
*   `Timeout` (float, default: `0.5`): This is a workaround to the [buffer parsing bugs](https://github.com/kristopolous/Streamdown/issues/4). By increasing the select timeout, the parser loop only gets triggerd on newline which means that having to resume from things like a code block, inside a list, inside a table, between buffers, without breaking formatting doesn't need to be done. It's a problem I'm working on (2025-04-01) and there will be bugs. Set this value to something like 3.0 and you'll avoid it with a pretty minor tradeoff.

Example:
```toml
[features]
CodeSpaces = false
Clipboard = false
Margin = 4
Timeout = 3.0
```

## Demo
Do this

    $ ./tester.sh tests/*md | streamdown/sd.py

Certainly room for improvement and I'll probably continue to make them

## Install from source
At least one of these should work, hopefully

    $ pipx install -e .
    $ pip install -e .
    $ uv pip install -e . 
