"""YOUTRACK."""

import logging
import os
import pickle
import sys

import click

from vm_clockify.service.api_clockify_service import IssueTime
from vm_clockify.service.api_youtrack_service import ApiYoutrackService
from vm_clockify.utils.config import settings
from vm_clockify.utils.utils_helper import Context, create_service_folder, pass_context, uri_validator


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
@click.group()
@click.option(
    "-k",
    "--key",
    type=str,
    help=f"api key for youtrack [{settings.YOUTRACK_API_KEY}]",
    default=settings.YOUTRACK_API_KEY,
    required=True,
)
@click.option(
    "-e",
    "--endpoint",
    type=str,
    help=f"only base url [{settings.YOUTRACK_API_ENDPOINT}]",
    default=settings.YOUTRACK_API_ENDPOINT,
    required=True,
)
@pass_context
def cli(ctx: Context, key: str, endpoint: str):
    """Youtrack-api usage command."""
    if uri_validator(endpoint):
        settings.YOUTRACK_API_KEY = key
        settings.YOUTRACK_API_ENDPOINT = endpoint
        ctx.service = ApiYoutrackService()
    else:
        logging.log(logging.WARNING, f'endpoint "{endpoint}" is not a valid url format')
        sys.exit(2)


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
@cli.command()
@pass_context
def upload(ctx: Context):
    """Will insert times collected from clockify into youtrack.

    HINT: run clockify times api first, else there are no records to be uploaded.
    """
    try:
        service: ApiYoutrackService = ctx.service
        issues: dict[str, IssueTime] = {}
        with open(f"{create_service_folder()}/{settings.CLOCKIFY_TMP_FILE}", "rb") as f:
            issues = pickle.load(f)
        service.upload(issues=issues)
        if os.path.exists(f"{create_service_folder()}/{settings.CLOCKIFY_TMP_FILE}"):
            os.remove(f"{create_service_folder()}/{settings.CLOCKIFY_TMP_FILE}")
    except KeyboardInterrupt as k:
        logging.log(logging.DEBUG, f"process interrupted! ({k})")
        sys.exit(5)
    except Exception as e:
        logging.log(logging.CRITICAL, e, exc_info=True)
        sys.exit(2)
