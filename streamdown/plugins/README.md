# Streamdown Plugins

Streamdown contains a simple and hopefully not too painful plugin system

``` python
def Plugin(line in, State, Style):
  return None | [ ansi escaped and formatted line, ]
```

* If None, its assumed the plugin is uninterested. 
* If it's an array, it's assumed it should be yielded and no other code should be run
* If it's non-None then it receives priority as the first plugin called until it returns none, claiming it's done with the code
* It's responsible for maintaining its own state. 
* The State and Style are from the main program if it chooses to observe it.

Check the files, they're pretty small and should be fairly self explanatory.

