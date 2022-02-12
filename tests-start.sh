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

echo 'install dev dependencies...'
python3 -m pip install -r requirements_dev.txt

echo 'run tests...'
bash ./scripts/format-imports.sh | tee ./scripts/logs/format-imports.log
bash ./scripts/test-cov-html.sh | tee ./scripts/logs/test-cov-html.log
bash ./scripts/test.sh "$@" | tee ./scripts/logs/test.log
bash ./scripts/lint.sh | tee ./scripts/logs/lint.log

exit 0
