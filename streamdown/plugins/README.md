# Streamdown Plugins

See [#10](https://github.com/kristopolous/Streamdown/issues/10) for the rewrite effort.

Streamdown contains a simple and hopefully not too painful plugin system

``` python
def Plugin(line_in, State):
  # state.in_level = "block" | "inline"

  return None | {
    state: "running" | "done"
    pre: <unformatted>,
    res: <ansi escaped formatted content>,
    post: <unformatted>
  }
```


* If None, its assumed the plugin is uninterested in the incoming line.
* If it's an object
* If it's non-None then it receives priority as the first plugin called untel it returns none, claiming it's done with the parsing
* It's responsible for maintaining its own state. 
* The State is from the main program if it chooses to observe it. The Style parameter is in State.style

The important caveat is this thing is truly streaming. 
```
You may get totally part
ial text li
ke this and then have to reco
nstruct it.
```

It is up to you how you'd like to yield it. You can buffer and wait for the whole segment if you need to, emit based on lines, whatever is needed. That's up to you!

There's a few tricks for tricky situations tht are used in the main sd.py and those are all available to you via state and yield hacks.

Check the files, they're pretty small and should be fairly self explanatory.

