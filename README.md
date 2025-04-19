# Streamdown

[![PyPI version](https://badge.fury.io/py/streamdown.svg)](https://badge.fury.io/py/streamdown)

Streamdown is the streaming markdown renderer for the terminal that rocks.
This will work with [simonw's llm](https://github.com/simonw/llm). You even get full readline and keyboard navigation support.

It's fully streaming and does not block
![Streamdown is Amazing](https://github.com/user-attachments/assets/268cb340-78cc-4df0-a773-c5ac95eceeeb)

### Provides clean copyable code for long code lines
You may have noticed that other, *inferior* renderers will inject line breaks when copying code that wraps around. We're better and now, you can be as well.
![Handle That Mandle](https://github.com/user-attachments/assets/a27aa70c-f691-4796-84f0-c2eb18c7de23)

### Supports images
Here's kitty and alacritty. Try to do that in glow...
![doggie](https://github.com/user-attachments/assets/9a392929-b6c2-4204-b257-e09305acb7af)

### Does OSC 8 links for modern terminals (and optionally OSC 52 for clipboard)
[links.webm](https://github.com/user-attachments/assets/a5f71791-7c58-4183-ad3b-309f470c08a3)

### Tables are carefully supported
![table](https://github.com/user-attachments/assets/dbe3d13e-6bac-4f45-bf30-f1857ed98898)

As well as everything else...

![dunder](https://github.com/user-attachments/assets/d41d7fec-6dec-4387-b53d-f2098f269a5e)

### Colors are highly (and quickly) configurable for people who care a lot, or just a little.
![configurable](https://github.com/user-attachments/assets/04b36749-4bb8-4c14-9758-84eb6e19b704)

### Has a [Plugin](https://github.com/kristopolous/Streamdown/tree/main/streamdown/plugins) system to extend the parser and renderer.
For instance, here is the [latex plugin](https://github.com/kristopolous/Streamdown/blob/main/streamdown/plugins/latex.py) doing math inside a table:
![calc](https://github.com/user-attachments/assets/0b0027ca-8ef0-4b4a-b4ae-e36ff623a683)


## Configuration


Streamdown uses a TOML configuration file located at `~/.config/streamdown/config.toml` (following the XDG Base Directory Specification). If this file does not exist upon first run, it will be created with default values. 

Here are the sections:

**`[style]`**

Defines the base Hue (H), Saturation (S), and Value (V) from which all other palette colors are derived. The defaults are [at the beginning of the source](https://github.com/kristopolous/Streamdown/blob/main/streamdown/sd.py#L33).

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
*   `Syntax` (string, default `monokai`): This is the syntax [highlighting theme which come via pygments](https://pygments.org/styles/).

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
*   `Logging` (boolean, default: `false`): Enables logging to tmpdir (/tmp/sd) of the raw markdown for debugging and bug reporting. The logging uses an emoji as a record separator so the actual streaming delays can be simulated and replayed. If you use the `filename` based invocation, that is to say, `sd <filename>`, this type of logging is always off.
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

## Invocation
The most exciting feature here is `--exec` with it you can do full readline support like this:

     $ sd --exec "llm chat"

And now you have all your readline stuff. It's pretty great.

```shell
Streamdown - A markdown renderer for modern terminals

positional arguments:
  filenameList          Input file to process (also takes stdin)

options:
  -h, --help            show this help message and exit
  -l LOGLEVEL, --loglevel LOGLEVEL
                        Set the logging level
  -c COLOR, --color COLOR
                        Set the hsv base: h,s,v
  -w WIDTH, --width WIDTH
                        Set the width
  -e EXEC, --exec EXEC  Wrap a program for more 'proper' i/o handling

```

## Demo
Do this

    $ ./streamdown/sd.py tests/*md

## Install from source
After the git clone least one of these should work, hopefully. it's using the modern uv pip tool.

    $ pipx install -e .
    $ pip install -e .
    $ uv pip install -e . 

### Future work

#### CSS
I'm really considering using `tinycss2` and making an actual stylesheet engine. This is related to another problem - getting a modern HTML renderer in the terminal that is actually navigable. I *think* it's probably a separate project.

#### scrape
This is already partially implemented. The idea is every code block can get extracted and put in a directory so you can have a conversation to generate every piece of a project, similar to Aider, Claude or Goose,  but in the most hands-off yet still convenient way possible.

