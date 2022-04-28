# Python CLI Clockify API

```sh
    MVladislav
```

[![Python DEV CI](https://github.com/MVladislav/vm-clockify/actions/workflows/python-dev.yml/badge.svg)](https://github.com/MVladislav/vm-clockify/actions/workflows/python-dev.yml)
[![Create Release](https://github.com/MVladislav/vm-clockify/actions/workflows/python-release.yml/badge.svg)](https://github.com/MVladislav/vm-clockify/actions/workflows/python-release.yml)

---

- [Python CLI Clockify API](#python-cli-clockify-api)
  - [information](#information)
    - [clockify task-name and project-name usage](#clockify-task-name-and-project-name-usage)
    - [config](#config)
  - [install](#install)
    - [DEBUG](#debug)
  - [code quality and git](#code-quality-and-git)
    - [pre-commit](#pre-commit)
    - [manual test run](#manual-test-run)

---

project to use api from [clockify](https://clockify.me/developers-api) to collect work-time

in a combined way by `[day, project, task]`

## information

### clockify task-name and project-name usage

this script will parse the **task**-name and **project**-name usage and search for brackets like `[(.*?)]`
where you can write **issue-id** in it, for example:

```txt
some description task [ISSUE-666]
```

This **issue-id** can than be used to import the time into services like youtrack

### config

copy the `.env` file and add your values

```sh
$cp .env_template .env
```

## install

```sh
$pip3 install .
```

### DEBUG

```sh
$python3 -m venv ./venv
$source venv/bin/activate
$pip3 install -v --editable .
```

---

## code quality and git

### pre-commit

run:

```sh
$git config --local core.hooksPath .git/hooks
$pre-commit install
```

### manual test run

```sh
$mypy vm_clockify
$flake8 vm_clockify
$pytest --cov=tests
$tox
```
