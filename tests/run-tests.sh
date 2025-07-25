#!/bin/bash
{ 
    for i in *.md; do
        echo "($i: [[ start ]])"
        ../streamdown/sd.py $i | sed "s/^/$i: /g"

        echo "($i: [[ end ]])"
    done
}
