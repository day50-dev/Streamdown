# Streamdown

I needed a streaming Markdown TUI CLI shell parser and honestly all the ones I found sucked. They were broken or janky in some kind of way. So here we go:

[simplescreenrecorder-2025-03-12_17.58.07.webm](https://github.com/user-attachments/assets/de4860d5-dd0e-411f-bda3-e3d60deb7938)

This will work with [swillison's llm](https://github.com/simonw/llm) unlike with [richify.py](https://github.com/gianlucatruda/richify) which jumps around the page or shows useless elipses or [glow](https://github.com/charmbracelet/glow) which buffers everything, this streams and does exactly what you want.

There's nothing too fancy about it other than that it works.
![2025-03-12_19-07](https://github.com/user-attachments/assets/eeb46c66-6ce3-41d6-94d4-89a7aefdc470)


Certainly room for improvement.

 * tables don't currently stream. it's actually a sophisticated problem. i've got a solution but I want to just have the llm do it without having to think about it. I am theoretically not always this lazy.

* ingest the first 2 rows. compute the division from there and do wrap on the cells

* alternatively do equal width and permit sub optimal widths.

* lastly, this is inspired from sqlite, we can do key/value rows as individual tables, which changes the layout but makes large row tables not cascade down the screen in some wraparound mess.
