#!/bin/sh -e
set -x

python3 -m autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place vm_clockify --exclude=__init__.py
python3 -m black vm_clockify
python3 -m isort --recursive --apply vm_clockify
