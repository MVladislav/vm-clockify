"""MAIN."""

import logging
import os

import click

from .utils.config import settings
from .utils.log_helper import LogHelper

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
# Program Header
# Basic user interface header
print(  # noqa: T201
    r"""    __  ____    ____          ___      __
   /  |/  / |  / / /___ _____/ (_)____/ /___ __   __
  / /|_/ /| | / / / __ `/ __  / / ___/ / __ `/ | / /
 / /  / / | |/ / / /_/ / /_/ / (__  ) / /_/ /| |/ /
/_/  /_/  |___/_/\__,_/\__,_/_/____/_/\__,_/ |___/"""
)
print("**************** 4D 56 6C 61 64 69 73 6C 61 76 *****************")  # noqa: T201
print("****************************************************************")  # noqa: T201
print("* Copyright of MVladislav, 2024                                *")  # noqa: T201
print("* https://mvladislav.online                                    *")  # noqa: T201
print("* https://github.com/MVladislav                                *")  # noqa: T201
print("****************************************************************")  # noqa: T201
print()  # noqa: T201


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
class ComplexCLI(click.MultiCommand):
    """ComplexCLI."""

    def list_commands(self, ctx):
        """ComplexCLI."""
        rv = []
        for filename in os.listdir(os.path.join(os.path.dirname(__file__), "./commands")):
            if filename.endswith(".py") and not filename.startswith("__"):
                rv.append(filename[:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        """ComplexCLI."""
        try:
            mod = __import__(f"vm_clockify.commands.{name}", None, None, ["cli"])
            return mod.cli

        except ImportError as e:
            logging.log(logging.CRITICAL, e)
        return None


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
    "ignore_unknown_options": True,
    "auto_envvar_prefix": "COMPLEX",
}


@click.command(cls=ComplexCLI, context_settings=CONTEXT_SETTINGS)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help=f"Enables verbose mode [{settings.LOGGING_VERBOSE}]",
    default=settings.LOGGING_VERBOSE,
)
@click.option(
    "-l",
    "--logging-level",
    type=click.Choice(
        [
            "CRITICAL",
            "ERROR",
            "WARNING",
            "SUCCESS",
            "NOTICE",
            "INFO",
            "VERBOSE",
            "DEBUG",
            "SPAM",
        ]
    ),
    help=f"which log level to use [{settings.LOGGING_LEVEL}]",
    default=settings.LOGGING_LEVEL,
)
@click.option(
    "--home",
    type=click.Path(writable=True),
    help=f"home path to save scannes [{settings.BASE_PATH}]",
    default=settings.BASE_PATH,
)
@click.option(
    "-p",
    "--project",
    type=str,
    help=f"project name to store result in [{settings.PROJECT_NAME}]",
    default=settings.PROJECT_NAME,
)
@click.option(
    "-dsp",
    "--disable-split-project",
    is_flag=True,
    help="disable splitting folder struct by project [false]",
)
@click.option(
    "-dsh",
    "--disable-split-host",
    is_flag=True,
    help="disable splitting folder struct by host [false]",
)
def cli(
    verbose: int,
    logging_level: str,
    home: str,
    project: str,
    disable_split_project: bool,
    disable_split_host: bool,
):
    """Welcome to {PROJECT_NAME}.

    Example: "{PROJECT_NAME} -vv -p 'nice project' -dsh --home . <COMMAND> [OPTIONS] <COMMAND> [OPTIONS]"
    """
    # SET: default global values
    settings.LOGGING_VERBOSE = verbose
    settings.LOGGING_LEVEL = logging_level
    settings.BASE_PATH = home
    settings.PROJECT_NAME = project
    settings.DISABLE_SPLIT_PROJECT = disable_split_project
    settings.DISABLE_SPLIT_HOST = disable_split_host
    # INIT: log helper global
    LogHelper(logging_verbose=settings.LOGGING_VERBOSE, logging_level=settings.LOGGING_LEVEL)
    logging.log(logging.DEBUG, "init start_up...")
    settings.print()
