#!/usr/bin/env zsh
idx=${1:-1}
../streamdown/sd.py <(./chunk-buffer.sh /tmp/sd/$UID/dbg*(om[$idx]))
