#!/usr/bin/env bash
set -x

python3 -m mypy app --cache-dir ./scripts/logs/.mypy_cache
python3 -m black app --check
python3 -m isort --recursive --check-only app
python3 -m flake8 app --count --select=E9,F63,F7,F82 --show-source --statistics
python3 -m flake8 app --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
python3 -m pylint --rcfile=setup.cfg "$(find app -regextype egrep -regex '(.*.py)$')"
# python3 -m tox --workdir ./scripts/logs/.tox
