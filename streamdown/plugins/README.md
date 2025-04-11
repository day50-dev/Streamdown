# Streamdown Plugins

Streamdown contains a simple and hopefully not too painful plugin system

``` python
def Plugin(line in, State, Style):
  return None | [ ansi escaped and formatted line, ]
```

* If None, its assumed the plugin is uninterested in the incoming line.
* If it's an array, it's assumed it should be yielded and no other code should be run
* If it's non-None then it receives priority as the first plugin called until it returns none, claiming it's done with the parsing
* It's responsible for maintaining its own state. 
* The State and Style are from the main program if it chooses to observe it.

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

