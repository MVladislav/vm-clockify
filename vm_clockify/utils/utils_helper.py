"""UTILS HELPER."""

import logging
import os
from pathlib import Path
import re
import sys
from typing import Any
import unicodedata
from urllib.parse import urlparse

import click
import httpx

from vm_clockify.utils.config import settings


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
class Context:
    """CONTEXT."""

    def __init__(self):
        """INIT CONTEXT."""
        logging.log(logging.DEBUG, "init context...")
        self.service: Any = None


pass_context = click.make_pass_decorator(Context, ensure=True)


# --------------------------------------------------------------------------
#
# path | folder | file - helper
#
# --------------------------------------------------------------------------


def create_service_folder(
    name: str | None = None,
    host: str | None = None,
    split_host: bool | None = None,
    split_project: bool | None = None,
) -> str:
    """Create a folder with name optional host under base path."""
    try:
        path = create_service_path(host=host, split_host=split_host, split_project=split_project)
        path = f"{path}/{name}" if name is not None else path
        if path.startswith("./"):
            path = f"{os.getcwd()}{path[1:]}"
        if create_folder(path):
            logging.log(logging.DEBUG, f"new folder created:: {path}")
            return path

        logging.log(logging.ERROR, f'failed to create path "{path}", check permission')
    except Exception as e:
        logging.log(logging.CRITICAL, e, exc_info=True)
    sys.exit(1)


def create_folder(path: str) -> bool:
    """Create a folder under giving path."""
    try:
        Path(path).mkdir(parents=True, exist_ok=True, mode=0o700)
        return True

    except Exception as e:
        logging.log(logging.CRITICAL, e, exc_info=True)
    return False


def create_service_path(
    host: str | None = None,
    split_host: bool | None = None,
    split_project: bool | None = None,
) -> str:
    """Create a path name, will used in call by "create_service_folder"."""
    split_host = not settings.DISABLE_SPLIT_HOST if split_host is None else split_host
    split_project = not settings.DISABLE_SPLIT_PROJECT if split_project is None else split_project
    if split_host and host is not None:
        host = slugify(host)
        host = "" if host is None else f"/{host}"
    else:
        host = ""
    project = ("" if settings.PROJECT_NAME is None else f"/{settings.PROJECT_NAME}") if split_project else ""
    if settings.BASE_PATH[-1] == "/":
        settings.BASE_PATH = settings.BASE_PATH[:-1]
    return f"{settings.BASE_PATH}{project}{host}"


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------


def uri_validator(url: str) -> str | None:
    """No desc."""
    try:
        if url.endswith("/"):
            url = url[:-1]
        result = urlparse(url)
        if all([result.scheme, result.netloc]):
            return url

    except Exception as e:
        logging.log(logging.WARNING, e)
    return None


def url_checker(url) -> bool:
    """No desc."""
    try:
        get = httpx.get(url, timeout=5)
        logging.log(logging.DEBUG, f"{url}: returns '{get.status_code}'")
        # if get.status_code == 200:
        return True

    except httpx.RequestError as e:
        logging.log(logging.DEBUG, f"{url}: fails with '{e}'")
    except Exception as e:
        logging.log(logging.DEBUG, f"{url}: fails with [{type(e)}] '{e}'")
    return False


def slugify(value: str | None, allow_unicode: bool = False) -> str | None:
    """No desc."""
    """https://github.com/django/django/blob/main/django/utils/text.py"""
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")
