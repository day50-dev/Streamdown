# StreamingMarkdown

[simplescreenrecorder-2025-03-12_01.10.42.webm](https://github.com/user-attachments/assets/47e7eaea-74a4-49cf-bdac-14aeef3dabb0)


I needed a streaming Markdown TUI CLI shell parser and honestly all the ones I found sucked. They were broken or janky in some kind of way. So I spent about 14 million tokens and did some minor human tweaks over the course of about 8 hours, here we go:
![sshot](https://github.com/user-attachments/assets/43cf7f5f-d11f-467e-8186-d5df9de84fb0)

This will work with [swillison's llm](https://github.com/simonw/llm) unlike with richify.py which jumps around the page or shows useless elipss or glow which buffers everything, this streams and does exactly what you want.

There's nothing too fancy about it other than that it works.

Certainly room for improvement.
