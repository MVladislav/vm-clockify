# Python CLI Clockify API

```sh
    MVladislav
```

[![Python DEV CI](https://github.com/MVladislav/vm-clockify/actions/workflows/python-dev.yml/badge.svg)](https://github.com/MVladislav/vm-clockify/actions/workflows/python-dev.yml)
[![Create Release](https://github.com/MVladislav/vm-clockify/actions/workflows/python-release.yml/badge.svg)](https://github.com/MVladislav/vm-clockify/actions/workflows/python-release.yml)

---

- [Python CLI Clockify API](#python-cli-clockify-api)
  - [information](#information)
    - [example usage](#example-usage)
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

### example usage

get 2-days of work from clockify with start day `2023-02-07`

- `-d 1` => will return 2 days, the requested day + the day before
- `-p 1000` => allow to include 1000 entries from clockify over 2 days
- `-sp '2023-02-07'` => the start day to collect work from

```sh
$vm-clockify clockify times -d 1 -p 1000 -sp '2023-02-07'
```

upload the gathered work from command above into youtrack

```sh
$vm-clockify youtrack upload
```

### clockify task-name and project-name usage

this script will parse the **task**-name and **project**-name usage and search for brackets like `<DESCRIPTION> [<URL-PARAM-SYNTAX>]`
where you can write **issue-id** in it, for example:

> only the last bracket in a description will be checked

- `i` => issue-id
- `t` => issue-type-name

```txt
some description task [i=ISSUE-666]
```

or

```txt
some description task [i=ISSUE-666&t=Training]
```

This **issue-id** can than be used to import the time into services like youtrack, and **issue-type-name** to mark the issue in youtrack with an type.

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
