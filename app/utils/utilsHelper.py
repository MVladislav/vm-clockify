import logging
import os
import re
import socket
import sys
import unicodedata
from shutil import which
from subprocess import check_call
from typing import Any, Dict, List, Union
from urllib.parse import urlparse

import click
import requests
from progressbar import ProgressBar


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
class Context:
    progress: Dict[int, ProgressBar] = {}

    def __init__(self):
        logging.log(logging.DEBUG, 'init context...')
        self.service: Any = None


pass_context = click.make_pass_decorator(Context, ensure=True)


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
def group(flat: List[Any], size: int) -> List[Any]:
    """
    group list a flat list into a matrix of "size"
    """
    return [flat[i: i + size] for i in range(0, len(flat), size)]


def normalize_caseless(text: str) -> str:
    """
    lowercase a string, for any unicode
    """
    return unicodedata.normalize("NFKD", text.casefold())


def slugify(value: Union[str, None], allow_unicode: bool = False) -> Union[str, None]:
    """
    https://github.com/django/django/blob/main/django/utils/text.py
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode(
            "ascii"
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")




# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
def in_sudo_mode() -> None:
    """
    If the user doesn't run the program with super user privileges, don't allow them to continue.
    """
    try:
        if "SUDO_UID" not in os.environ.keys():
            logging.log(logging.ERROR, "Try running this program with sudo.")
            sys.exit(1)
    except Exception as e:
        logging.log(logging.CRITICAL, e, exc_info=True)


def prompt_sudo() -> bool:
    """
    will prompt as for sudo root pw if user is not in sudo mode
    """
    try:
        if os.geteuid() != 0:
            msg = 'you run service with "-s" in "sudo" mode, you need enter sudo password to use some functions\n--> [sudo] password for %u: '
            return check_call(f'sudo -v -p "{msg}"', shell=True) == 0

        else:
            return True

    except Exception as e:
        logging.log(logging.CRITICAL, e, exc_info=True)
    return False


def is_tool(name: str) -> bool:
    """
    Check whether `name` is on PATH and marked as executable.
    """
    return which(name) is not None




# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
def geo() -> Union[str, None]:
    """
    This is a geo test example
    """
    try:
        from app.utils.locater import Locator
        return Locator().check_database()

    except Exception as e:
        logging.log(logging.CRITICAL, e, exc_info=True)
    return None


def get_ip_address() -> Union[str, None]:
    IP: Union[str, None] = None
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as st:
            st.connect(("10.255.255.255", 1))
            IP = st.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    return IP


def uri_validator(url: str) -> Union[str, None]:
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
    try:
        get = requests.get(url, timeout=5)
        logging.log(logging.DEBUG, f"{url}: returns '{get.status_code}'")
        # if get.status_code == 200:
        return True

    except requests.exceptions.RequestException as e:
        logging.log(logging.DEBUG, f"{url}: fails with '{e}'")
    except Exception as e:
        logging.log(logging.DEBUG, f"{url}: fails with [{type(e)}] '{e}'")
    return False




# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
def define_option_list(
    options: str,
    default_options: List[Any] = [],
    options_append: bool = False,
    # default_split_by: str = ",",
) -> List[Any]:
    """
    defines a list of option to use in a callable service
    to define how to create this list
    by:
        - create it from a default only
        - create it from params only
        - create it by combine default and params
    """
    try:
        result: List[Any] = []
        # add options from params
        if options is not None and not options_append:
            result = [options]  # .split(default_split_by)
        # add options from params to existing options
        elif options is not None and options_append:
            result = default_options + [options]  # .split(default_split_by)
        # use existing options
        else:
            result = default_options
        return result

    except Exception as e:
        logging.log(logging.CRITICAL, e, exc_info=True)
    return []
