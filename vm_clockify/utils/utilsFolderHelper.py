import logging
import os
import sys
from pathlib import Path
from typing import Union

from vm_clockify.utils.config import settings
from vm_clockify.utils.utilsHelper import slugify


# --------------------------------------------------------------------------
#
# path | folder | file - helper
#
# --------------------------------------------------------------------------
def get_user_path() -> str:
    """
        returns path to user home
    """
    return str(Path.home())


def create_service_folder(
    name: Union[str, None] = None,
    host: Union[str, None] = None,
    split_host: Union[bool, None] = None,
    split_project: Union[bool, None] = None,
) -> str:
    """
        creates a folder with name optional host under base path
    """
    try:
        path = create_service_path(
            host=host, split_host=split_host, split_project=split_project
        )
        path = f"{path}/{name}" if name is not None else path
        if path.startswith("./"):
            path = f"{os.getcwd()}{path[1:]}"
        if create_folder(path):
            logging.log(logging.DEBUG, f"new folder created:: {path}")
            return path

        else:
            logging.log(
                logging.ERROR, f'failed to create path "{path}", check permission'
            )
    except Exception as e:
        logging.log(logging.CRITICAL, e, exc_info=True)
    sys.exit(1)


def create_folder(path: str) -> bool:
    """
        create a folder under giving path
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True, mode=0o700)
        return True

    except Exception as e:
        logging.log(logging.CRITICAL, e, exc_info=True)
    return False


def create_service_path(
    host: Union[str, None] = None,
    split_host: Union[bool, None] = None,
    split_project: Union[bool, None] = None,
) -> str:
    """
        creates a path name, will used in call by "create_service_folder"
    """
    split_host = not settings.DISABLE_SPLIT_HOST if split_host is None else split_host
    split_project = not settings.DISABLE_SPLIT_PROJECT if split_project is None else split_project
    if split_host and host is not None:
        host = slugify(host)
        host = "" if host is None else f"/{host}"
    else:
        host = ""
    if split_project:
        PROJECT = "" if settings.PROJECT_NAME is None else f"/{settings.PROJECT_NAME}"
    else:
        PROJECT = ""
    if settings.BASE_PATH[-1] == "/":
        settings.BASE_PATH = settings.BASE_PATH[:-1]
    return f"{settings.BASE_PATH}{PROJECT}{host}"
