# StreamingMarkdown

I needed a streaming Markdown TUI CLI shell parser and honestly all the ones I found sucked. They were broken or janky in some kind of way. So here we go:

[simplescreenrecorder-2025-03-12_17.58.07.webm](https://github.com/user-attachments/assets/de4860d5-dd0e-411f-bda3-e3d60deb7938)

![sshot](https://github.com/user-attachments/assets/43cf7f5f-d11f-467e-8186-d5df9de84fb0)

This will work with [swillison's llm](https://github.com/simonw/llm) unlike with richify.py which jumps around the page or shows useless elipss or glow which buffers everything, this streams and does exactly what you want.

There's nothing too fancy about it other than that it works.

Certainly room for improvement.

 * tables don't currently stream. it's actually a sophisticated problem. i've got a solution but I want to just have the llm do it without having to think about it. I am theoretically not always this lazy.

* ingest the first 2 rows. compute the division from there and do wrap on the cells

* alternatively do equal width and permit sub optimal widths.

* lastly, this is inspired from sqlite, we can do key/value rows as individual tables, which changes the layout but makes large row tables not cascade down the screen in some wraparound mess.
