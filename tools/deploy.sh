#!/bin/bash
set -eEuo pipefail
version=$(grep version pyproject.toml  | cut -d '"' -f 2)
tag_update() {
    git tag -m v$version v$version
    git push --tags
}
pipy() {
    for i in pip hatch build; do
        pip install --upgrade $i
    done
    python3 -m build .
    twine upload dist/*${version}*
}
tag_update
pipy
