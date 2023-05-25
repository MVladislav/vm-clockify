#!/bin/sh -e
set -x

# Sort imports one per line, so autoflake can remove unused imports
python3 -m isort --force-single-line-imports --src vm_clockify .
sh ./scripts/format.sh
