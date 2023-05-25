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

setup `.env` file with following possible params:

```env
# optional
LOGGING_LEVEL=DEBUG
LOGGING_VERBOSE=3

# need to be correct set, to work with youtrack correct
TIME_ZONE=Europe/Berlin

# optional
WORK_TIME_DEFAULT_ISSUE=<ADD_ISSUE_HERE>
WORK_TIME_DEFAULT_COMMENT=<ADD_TEXT_HERE>

# -> if get worktime from clockify is used
# https://clockify.me/user/settings
CLOCKIFY_API_KEY=<ADD_KEY_HERE>
# get by use command 'api user'
CLOCKIFY_API_WORKSPACE_ID=<ADD_ID_HERE>
CLOCKIFY_API_USER_ID=<ADD_ID_HERE>

# -> if upload to youtrack is used
# https://www.jetbrains.com/help/youtrack/devportal/Manage-Permanent-Token.html#obtain-permanent-token
YOUTRACK_API_KEY=<ADD_HERE>
YOUTRACK_API_ENDPOINT=<ADD_HERE>

# -> if upload to landwehr is used
LANDWEHR_API_URL=<ADD_HERE>
LANDWEHR_API_ENDPOINT=/index.php
LANDWEHR_COMPANY=<ADD_HERE>
LANDWEHR_MAND_NR=<ADD_HERE>
LANDWEHR_USERNAME=<ADD_HERE>
LANDWEHR_PASSWORD=<ADD_HERE>
```

## install

```sh
$python3 -m pip install .
```

or

```sh
$python3 -m venv ./venv
$source venv/bin/activate
$python3 -m pip install -v --editable .
```
