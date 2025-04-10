#!/bin/bash
TIMEOUT=${TIMEOUT:-0.1}
while [[ $# -gt 0 ]]; do
    echo "## File: $1"
    echo "----"
    for i in $(seq 1 $(cat $1 | wc -l)); do
        head -$i $1 | tail -1
        sleep $TIMEOUT
    done
    shift
done

