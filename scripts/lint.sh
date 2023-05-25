#!/usr/bin/env bash
set -x

python3 -m mypy vm_clockify --cache-dir ./scripts/logs/.mypy_cache
python3 -m black vm_clockify --check
python3 -m isort --check-only --src vm_clockify .
python3 -m flake8 vm_clockify --count --select=E9,F63,F7,F82 --show-source --statistics
python3 -m flake8 vm_clockify --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
# python3 -m pylint --rcfile=setup.cfg "$(find vm_clockify -regextype egrep -regex '(.*.py)$')"
# python3 -m tox --workdir ./scripts/logs/.tox
