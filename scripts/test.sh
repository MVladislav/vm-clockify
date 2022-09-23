#!/usr/bin/env bash

set -e
set -x

pytest --cov=vm_clockify --cov-report=term-missing vm_clockify/tests "${@}"
