FROM python:3.9-slim

# ------------------------------------------------------------------------------

# SET version label
ARG BUILD_DATE=latest
ARG VERSION=0.0.1
LABEL build_version="MVladislav version:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL maintainer="MVladislav"

# ------------------------------------------------------------------------------

# SET env
ENV DEBIAN_FRONTEND=noninteractive
# Prevents Python from writing pyc files to disc (equivalent to python -B option)
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr (equivalent to python -u option)
ENV PYTHONUNBUFFERED=1

# SET env for is docker, used in setup script
ENV IS_DOCKER=true
# SET not use venv in docker
ENV IS_VENV=false

# ------------------------------------------------------------------------------

# UPGRADE python pip
RUN python3 -m pip install --upgrade pip

# SET work dir
WORKDIR /vm-clockify/

# GET all file
COPY ./ ./

# SET project arguments
ARG PROJECT_NAME=vm-clockify
ARG ENV_MODE=KONS
ARG LOGGING_LEVEL=DEBUG
ARG LOGGING_VERBOSE=3

RUN mkdir -p /vm-clockify/scans/
ARG VM_BASE_PATH="/vm-clockify/scans/"

# ------------------------------------------------------------------------------

# INSTALL app with dependencies
RUN pip3 install --no-cache-dir .

# CLEAN up
RUN \
  apt-get clean \
  && rm -rf /var/lib/apt/lists/*

ENV PATH=/root/.local/bin/:$PATH
ENV PYTHONPATH=/usr/lib/python3/dist-packages/:$PYTHONPATH

# ------------------------------------------------------------------------------

# finish
EXPOSE $PORT
