# Python CLI Clockify API

```sh
    MVladislav
```

---

- [Python CLI Clockify API](#python-cli-clockify-api)
  - [information](#information)
    - [config](#config)
  - [install](#install)
    - [DEBUG](#debug)
  - [run](#run)
    - [docker](#docker)

---

project to use api from [clockify](https://clockify.me/developers-api) to collect worktime

in a combined way by `[day, project, task]`

## information

to run an print in best mode, only if you use services like **youtrack** or **jira**,

write the **issue** name into **task** or **project** in brackets, like:

```txt
some description task [ISSUE-666]
```

this will be parsed and printed

### config

copy the `.env` file and add your values

```sh
$cp .env_template .env
```

## install

```sh
$pip3 install starlette && pip3 install .
```

### DEBUG

```sh
$python3 -m venv ./venv
$source venv/bin/activate
$pip3 install starlette && pip3 install -v --editable .
```

## run

### docker

run **docker-compose** build and up

```sh
$DOCKER_BUILDKIT=1 docker-compose build
$DOCKER_BUILDKIT=1 docker-compose up
```
