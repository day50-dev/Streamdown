#!/bin/bash
TIMEOUT=${TIMEOUT:-0.05}

while [[ $# -gt 0 ]]; do
    echo "## File: $1"
    echo -e "----\n\n"
    cat $1 | awk -v RS='🫣' '{ printf "%s", $0; system("sleep '$TIMEOUT'") }' 
    shift
done
