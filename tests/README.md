### Various streamdown tests

This is not a formal testing system but is more "showcase based" testing, driving features and looking at output.

There's two drivers:

 * chunk-buffer.sh: The `Logging` config of the `sd.py` parser injects a peeking emoji to specify when the `Timeout` was hit and the render cycle was run. This timeout can cause issues. chunk-buffer will re-ingest these for diagnostic purposes

 * line-buffer.sh: Some parts of the parser waits for newlines, and this tool will feed line by line.

They both accept a TIMEOUT env variable
