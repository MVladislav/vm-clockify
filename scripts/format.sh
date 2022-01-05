#!/bin/sh -e
set -x

python3 -m autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place app --exclude=__init__.py
python3 -m black app
python3 -m isort --recursive --apply app
