# Streamdown

[![PyPI version](https://badge.fury.io/py/streamdown.svg)](https://badge.fury.io/py/streamdown)

I needed a streaming Markdown renderer and I couldn't find one. So here we go. From the ground up. It's a bad idea but it has to be done.

[sd demo](https://github.com/user-attachments/assets/48dba6fa-2282-4be9-8087-a2ad8e7c7d12)


This will work with [simonw's llm](https://github.com/simonw/llm) unlike with [richify.py](https://github.com/gianlucatruda/richify) which rerenders the whole buffer and blocks with an elipses or [glow](https://github.com/charmbracelet/glow) which buffers everything, this streams and does exactly what it says.

## Some Features

#### Provides clean copyable code for long code blocks and short terminals. 
![copyable](https://github.com/user-attachments/assets/4a3539c5-b5d1-4d6a-8bce-032724d8909d)

#### Does OSC 8 links for modern terminals.

[links.webm](https://github.com/user-attachments/assets/a5f71791-7c58-4183-ad3b-309f470c08a3)


#### Doesn't consume characters like _ and * as style when they are in `blocks like this` because `_they_can_be_varaiables_`
![dunder](https://github.com/user-attachments/assets/d41d7fec-6dec-4387-b53d-f2098f269a5e)

#### Tables are carefully supported
![table](https://github.com/user-attachments/assets/dbe3d13e-6bac-4f45-bf30-f1857ed98898)

#### Colors are highly (and quickly) configurable for people who care a lot, or just a little.
![configurable](https://github.com/user-attachments/assets/04b36749-4bb8-4c14-9758-84eb6e19b704)


## Configuration
Streamdown uses a TOML configuration file located at `~/.config/streamdown/config.toml` (following the XDG Base Directory Specification). If this file does not exist upon first run, it will be created with default values. Here are the sections:

**`[style]`**

Defines the base Hue (H), Saturation (S), and Value (V) from which all other palette colors are derived. Due to limitations in TOML, these all must be floats (have a decimal point). The defaults are [at the beginning of the source](https://github.com/kristopolous/Streamdown/blob/main/streamdown/sd.py#L33).

*   `HSV`: [ 0.0 - 1.0, 0.0 - 1.0, 0.0 - 1.0 ] 
*   `Dark`: Multipliers for background elements, code blocks. 
*   `Grey`: Multipliers for blockquote and thinkblock. 
*   `Mid`: Multipliers for inline code backgrounds, table headers. 
*   `Symbol`: Multipliers for list bullets, horizontal rules, links. 
*   `Head`: Multipliers for level 3 headers. 
*   `Bright`: Multipliers for level 2 headers. 
*   `Margin` (integer, default: `2`): The left and right indent for the output. 
*   `Width` (integer, default: `0`): Along with the `Margin`, `Width` specifies the base width of the content, which when set to 0, means use the terminal width. See [#6](https://github.com/kristopolous/Streamdown/issues/6) for more details
*   `PrettyPad` (boolean, default: `false`): Uses a unicode vertical pad trick to add a half height background to code blocks. This makes copy/paste have artifacts. See [#2](https://github.com/kristopolous/Streamdown/issues/2). I like it on. But that's just me
*   `ListIndent` (integer, default: `2`): This is the recursive indent for the list styles.
*   `Syntax` (string, default `monokai`): This the syntax [highlighting theme which come via pygments](https://pygments.org/styles/).

Example:
```toml
[style]
HSV = [0.7, 0.5, 0.5]
Dark = { H = 1.0, S = 1.2, V = 0.25 } # Make dark elements less saturated and darker
Symbol = { H = 1.0, S = 1.8, V = 1.8 } # Make symbols more vibrant
```

**`[features]`**

Controls optional features:

*   `CodeSpaces` (boolean, default: `true`): Enables detection of code blocks indented with 4 spaces. Set to `false` to disable this detection method (triple-backtick blocks still work).
*   `Clipboard` (boolean, default: `true`): Enables copying the last code block encountered to the system clipboard using OSC 52 escape sequences upon exit. Set to `false` to disable.
*   `Logging` (boolean, default: `false`): Enables logging to tmpdir (/tmp/sd) of the raw markdown for debugging and bug reporting. The logging uses an emoji as a record separator so the actual streaming delays can be simulated and replayed.
*   `Timeout` (float, default: `0.5`): This is a workaround to the [buffer parsing bugs](https://github.com/kristopolous/Streamdown/issues/4). By increasing the select timeout, the parser loop only gets triggerd on newline which means that having to resume from things like a code block, inside a list, inside a table, between buffers, without breaking formatting doesn't need to be done. I assert (2025-04-09) this is no longer a bug. Feel free to turn on `Logging` and post an issue if you find a repeatable one. 

Example:
```toml
[features]
CodeSpaces = false
Clipboard = false
Margin = 4
Width = 120
Timeout = 1.0
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

### Future work

#### CSS
I'm really considering using `tinycss2` and making an actual stylesheet engine. This is related to another problem - getting a modern HTML renderer in the browser that actually works. I *think* it's probably a separate project.

#### scrape
This is already partially implemented. The idea is every code block can get extracted and put in a directory so you can have a conversation to generate every piece of a project, similar to Aider, Claude or Goose,  but in the most hands-off yet still convenient way possible.

#### exec
I'm trying to get a readline capable wrapper so that interaction is as transparent as possible. After many days of research I've given up on trying to hack it through tty/pty hijacking and pipes and decided it has to be a standard wrapper. This should be low effort.
