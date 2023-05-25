#!/usr/bin/env bash

set -e
set -x

rm -rf ./.mypy_cache
rm -rf ./scripts/logs/.mypy_cache
rm -rf ./scripts/logs/.tox
rm -rf ./build
rm -rf ./venv
rm -f ./scripts/logs/html_dir
rm -f ./scripts/logs/format-imports.log
rm -f ./scripts/logs/lint.log
rm -f ./scripts/logs/test-cov-html.log
rm -f ./scripts/logs/test.log

exit 0
