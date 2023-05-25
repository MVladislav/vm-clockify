import logging
from typing import Union

import verboselogs
from pydantic import BaseSettings
from starlette.config import Config
from stringcolor.ops import Bold


class Settings(BaseSettings):
    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------
    config = Config(".env")
    # --------------------------------------------------------------------------
    #
    # LOGGING CONFIG
    #
    # --------------------------------------------------------------------------
    PROJECT_NAME: str = config("PROJECT_NAME", default="vm-clockify")
    VERSION: str = config("VERSION", default="1.1.0")
    TIME_ZONE: str = config("TIME_ZONE", default="Europe/Berlin")
    # CRITICAL | ERROR | SUCCESS | WARNING | NOTICE | INFO | VERBOSE | DEBUG | SPAM | NOTSET
    LOGGING_LEVEL: str = config("LOGGING_LEVEL", default="DEBUG")
    # 0-4
    LOGGING_VERBOSE: int = config("LOGGING_VERBOSE", cast=int, default=0)
    # --------------------------------------------------------------------------
    #
    # BASE CONFIG
    #
    # --------------------------------------------------------------------------
    BASE_PATH: str = config("VM_BASE_PATH", default=".")
    DISABLE_SPLIT_PROJECT: bool = config(
        "DISABLE_SPLIT_PROJECT", cast=bool, default=False
    )
    DISABLE_SPLIT_HOST: bool = config("DISABLE_SPLIT_HOST", cast=bool, default=False)

    # ------------------------------------------------------------------------------
    #
    # GENERAL TIME SETTINGS
    #
    # ------------------------------------------------------------------------------
    WORK_TIME_DEFAULT_HOURS: int = config(
        "WORK_TIME_DEFAULT_HOURS", cast=int, default=8
    )
    WORK_TIME_DEFAULT_ISSUE: Union[str, None] = config(
        "WORK_TIME_DEFAULT_ISSUE", default=None
    )
    WORK_TIME_DEFAULT_COMMENT: Union[str, None] = config(
        "WORK_TIME_DEFAULT_COMMENT", default=None
    )
    # ------------------------------------------------------------------------------
    #
    # CLOCKIFY
    #
    # ------------------------------------------------------------------------------
    CLOCKIFY_API_ENDPOINT: str = config(
        "CLOCKIFY_API_ENDPOINT", default="https://api.clockify.me/api/v1"
    )
    CLOCKIFY_API_KEY: Union[str, None] = config("CLOCKIFY_API_KEY", default=None)
    CLOCKIFY_API_WORKSPACE_ID: Union[str, None] = config(
        "CLOCKIFY_API_WORKSPACE_ID", default=None
    )
    CLOCKIFY_API_USER_ID: Union[str, None] = config(
        "CLOCKIFY_API_USER_ID", default=None
    )
    CLOCKIFY_TMP_FILE: str = "times"
    # ------------------------------------------------------------------------------
    #
    # YOUTRACK
    #
    # ------------------------------------------------------------------------------
    # base url needed, entered as option on call
    YOUTRACK_API_ENDPOINT: Union[str, None] = config(
        "YOUTRACK_API_ENDPOINT", default=None
    )
    YOUTRACK_API_ENDPOINT_SUFFIX: Union[str, None] = "youtrack/api"
    YOUTRACK_API_KEY: Union[str, None] = config("YOUTRACK_API_KEY", default=None)
    # ------------------------------------------------------------------------------
    #
    # LANDWEHR
    #
    # ------------------------------------------------------------------------------
    LANDWEHR_API_URL: str = config("LANDWEHR_API_URL")
    LANDWEHR_API_ENDPOINT: str = config("LANDWEHR_API_ENDPOINT", default="/index.php")
    LANDWEHR_COMPANY: str = config("LANDWEHR_COMPANY")
    LANDWEHR_MAND_NR: str = config("LANDWEHR_MAND_NR")
    LANDWEHR_USERNAME: str = config("LANDWEHR_USERNAME")
    LANDWEHR_PASSWORD: str = config("LANDWEHR_PASSWORD")

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    class Config:
        case_sensitive = True

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def print(self) -> None:
        if self.LOGGING_LEVEL == logging.getLevelName(logging.DEBUG):
            print()
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            logging.log(
                verboselogs.VERBOSE,
                f"PROJECT_NAME           : {Bold(self.PROJECT_NAME)}",
            )
            logging.log(
                verboselogs.VERBOSE, f"VERSION                : {Bold(self.VERSION)}"
            )
            logging.log(
                verboselogs.VERBOSE,
                f"LOGGING-LEVEL          : {Bold(self.LOGGING_LEVEL)}",
            )
            logging.log(
                verboselogs.VERBOSE,
                f"LOGGING-VERBOSE        : {Bold(self.LOGGING_VERBOSE)}",
            )
            logging.log(
                verboselogs.VERBOSE,
                f"DISABLED SPLIT PROJECT : {Bold(self.DISABLE_SPLIT_PROJECT)}",
            )
            logging.log(
                verboselogs.VERBOSE,
                f"DISABLED SPLIT HOST    : {Bold(self.DISABLE_SPLIT_HOST)}",
            )
            # logging.log(
            #     verboselogs.VERBOSE,
            #     f'PROJECT-PATH           : {Bold(create_service_path(None))}{Bold("/")}',
            # )
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print()


settings = Settings()
