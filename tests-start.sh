#!/usr/bin/env bash
set -e

echo ''
printf "    __  ____    ____          ___      __ \n\
   /  |/  / |  / / /___ _____/ (_)____/ /___ __   __ \n\
  / /|_/ /| | / / / __ \`/ __  / / ___/ / __ \`/ | / / \n\
 / /  / / | |/ / / /_/ / /_/ / (__  ) / /_/ /| |/ / \n\
/_/  /_/  |___/_/\__,_/\__,_/_/____/_/\__,_/ |___/\n"
echo '**************** 4D 56 6C 61 64 69 73 6C 61 76 *****************'
echo '****************************************************************'
echo '* Copyright of MVladislav, 2021                                *'
echo '* https://mvladislav.online                                    *'
echo '* https://github.com/MVladislav                                *'
echo '* TESTING                                                      *'
echo '****************************************************************'
echo ''

echo "Install python venv and setup as source..."
python3 -m pip install virtualenv --break-system-packages
python3 -m venv venv
source "./venv/bin/activate"

echo 'Install base and dev dependencies..'
python3 -m pip install -r requirements.txt
python3 -m pip install -r requirements-dev.txt

echo 'Run checks...'
# Sort imports one per line, so autoflake can remove unused imports
python3 -m isort --force-single-line-imports --src vm_clockify . | tee ./logs/format-imports.log
python3 -m autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place vm_clockify --exclude=__init__.py | tee ./logs/format-imports.log
python3 -m black vm_clockify | tee ./logs/format-imports.log
python3 -m isort --src vm_clockify . | tee ./logs/format-imports.log

python3 -m mypy vm_clockify --cache-dir ./logs/.mypy_cache | tee ./logs/lint.log
python3 -m black vm_clockify --check | tee ./logs/lint.log
python3 -m isort --check-only --src vm_clockify . | tee ./logs/lint.log
python3 -m flake8 vm_clockify --count --select=E9,F63,F7,F82 --show-source --statistics | tee ./logs/lint.log
python3 -m flake8 vm_clockify --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics | tee ./logs/lint.log

# rm -rf ./.mypy_cache
# rm -rf ./logs/.mypy_cache
# rm -rf ./logs/.tox
# rm -rf ./build
# rm -rf ./venv
# rm -f ./logs/html_dir
# rm -f ./logs/format-imports.log
# rm -f ./logs/lint.log
# rm -f ./logs/test-cov-html.log
# rm -f ./logs/test.log

exit 0
