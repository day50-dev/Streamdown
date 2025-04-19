#!/bin/bash
TIMEOUT=${TIMEOUT:-0.35}

while [[ $# -gt 0 ]]; do
    echo "## File: $1"
    echo "----"
    cat $1 | awk -v RS='🫣' '{ printf "%s", $0; system("sleep '$TIMEOUT'") }' 
    shift
done
