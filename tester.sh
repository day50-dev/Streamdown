#!/bin/bash
byline() {
    while [[ $# -gt 0 ]]; do
        echo "## File: $1"
        echo "----"
        for i in $(seq 1 $(cat $1 | wc -l)); do
            head -$i $1 | tail -1
            sleep 0.1
        done
        shift
    done
}

bybreak() {
    while [[ $# -gt 0 ]]; do
        cat $1 | awk -v RS='🫣' '{ printf "%s", $0; system("sleep 0.4") }' 
        shift
    done
}
bybreak $*
