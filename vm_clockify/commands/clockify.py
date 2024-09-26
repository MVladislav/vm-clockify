"""Clockify."""

import datetime
import logging
import sys

import click

from vm_clockify.service.api_clockify_service import ApiClockifyService
from vm_clockify.utils.config import settings
from vm_clockify.utils.utils_helper import Context, pass_context, uri_validator


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
    help=f"api key for clockify [{settings.CLOCKIFY_API_KEY}]",
    default=settings.CLOCKIFY_API_KEY,
    required=True,
)
@click.option(
    "-e",
    "--endpoint",
    type=str,
    help=f"full api endpoint [{settings.CLOCKIFY_API_ENDPOINT}]",
    default=settings.CLOCKIFY_API_ENDPOINT,
    required=True,
)
@pass_context
def cli(ctx: Context, key: str, endpoint: str):
    """Clockify api usage command."""
    if uri_validator(endpoint):
        settings.CLOCKIFY_API_KEY = key
        settings.CLOCKIFY_API_ENDPOINT = endpoint
        ctx.service = ApiClockifyService()
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
def user(ctx: Context):
    """Clockify API will return some needed information from user for times-api."""
    try:
        service: ApiClockifyService = ctx.service
        service.user()
    except KeyboardInterrupt as k:
        logging.log(logging.DEBUG, f"process interrupted! ({k})")
        sys.exit(5)
    except Exception as e:
        logging.log(logging.CRITICAL, e, exc_info=True)
        sys.exit(2)


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
@cli.command()
@click.option(
    "-w",
    "--workspace-id",
    type=str,
    help=f"workspace to use [{settings.CLOCKIFY_API_WORKSPACE_ID}]",
    default=settings.CLOCKIFY_API_WORKSPACE_ID,
    required=True,
)
@click.option(
    "-u",
    "--user-id",
    type=str,
    help=f"user to use [{settings.CLOCKIFY_API_USER_ID}]",
    default=settings.CLOCKIFY_API_USER_ID,
    required=True,
)
@click.option(
    "-y",
    "--year",
    type=int,
    help=f"from until now or specific day, how much days to collect backwards [{datetime.datetime.now().year}]",
    default=datetime.datetime.now().year,
    required=True,
)
@click.option(
    "-m",
    "--month",
    type=int,
    help=f"from until now or specific day, how much days to collect backwards [{datetime.datetime.now().month}]",
    default=datetime.datetime.now().month,
    required=True,
)
@click.option(
    "-f",
    "--taken-free-days",
    type=int,
    help="free days taken as holiday for that month [0]",
    default=0,
    required=True,
)
@click.option(
    "-i",
    "--illness-days",
    type=int,
    help="illness days for that month [0]",
    default=0,
    required=True,
)
@pass_context
def remaining_days(
    ctx: Context,
    workspace_id: str,
    user_id: str,
    year,
    month,
    taken_free_days=0,
    illness_days=0,
):
    """Clockify pi will print you remaining work-time for a specific month in a year.

    HINT: run first user-api to get workspace ID and user ID
    """
    try:
        settings.CLOCKIFY_API_WORKSPACE_ID = workspace_id
        settings.CLOCKIFY_API_USER_ID = user_id
        service: ApiClockifyService = ctx.service
        service.remaining_monthly_work_time(
            workspace_id=workspace_id,
            user_id=user_id,
            year=year,
            month=month,
            taken_free_days=taken_free_days,
            illness_days=illness_days,
        )
    except KeyboardInterrupt as k:
        logging.log(logging.DEBUG, f"process interrupted! ({k})")
        sys.exit(5)
    except Exception as e:
        logging.log(logging.CRITICAL, e, exc_info=True)
        sys.exit(2)


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
@cli.command()
@click.option(
    "-w",
    "--workspace-id",
    type=str,
    help=f"workspace to use [{settings.CLOCKIFY_API_WORKSPACE_ID}]",
    default=settings.CLOCKIFY_API_WORKSPACE_ID,
    required=True,
)
@click.option(
    "-u",
    "--user-id",
    type=str,
    help=f"user to use [{settings.CLOCKIFY_API_USER_ID}]",
    default=settings.CLOCKIFY_API_USER_ID,
    required=True,
)
@click.option(
    "-d",
    "--days-to-subtract",
    type=int,
    help="from until now or specific day, how much days to collect backwards [0]",
    default=0,
    required=True,
)
@click.option(
    "-p",
    "--page-size",
    type=int,
    help="how much records should loaded (max 5000) [50]",
    default=50,
    required=True,
)
@click.option(
    "-sp",
    "--specific-day",
    type=str,
    help="specific day to start collect from (format: YYYY-MM-DD) [None]",
    default=None,
)
@click.option(
    "-ps",
    "--project-search",
    type=str,
    help="specific project name to filter for (offline filter) [None]",
    default=None,
)
@click.option(
    "-ts",
    "--task-search",
    type=str,
    help="specific task name to filter for (offline filter) [None]",
    default=None,
)
@click.option(
    "-c",
    "--combine",
    help="if similar tasks should be combined into one bigger described task [false]",
    is_flag=True,
)
@click.option(
    "-b",
    "--buffer",
    help="if a buffer issue should be auto calculated [false]",
    is_flag=True,
)
@click.option(
    "-td",
    "--time-details",
    help="list time details in the terminal output [false]",
    is_flag=True,
)
@click.option(
    "-tc",
    "--time-count",
    help="list time counters in the terminal output [true]",
    is_flag=True,
)
@pass_context
def times(
    ctx: Context,
    workspace_id: str,
    user_id: str,
    days_to_subtract: int,
    page_size: int,
    specific_day: str,
    project_search: str,
    task_search: str,
    combine: bool,
    buffer: bool,
    time_details: bool,
    time_count: bool,
):
    """Clockify api will print you work-time.

    HINT: run first user-api to get workspace ID and user ID
    """
    try:
        settings.CLOCKIFY_API_WORKSPACE_ID = workspace_id
        settings.CLOCKIFY_API_USER_ID = user_id
        service: ApiClockifyService = ctx.service
        service.times(
            workspace_id=workspace_id,
            user_id=user_id,
            days_to_subtract=days_to_subtract,
            page_size=page_size,
            specific_day=specific_day,
            project_name=project_search,
            task_name=task_search,
            combine=combine,
            buffer=buffer,
            time_details=time_details,
            time_count=not time_count,
        )
    except KeyboardInterrupt as k:
        logging.log(logging.DEBUG, f"process interrupted! ({k})")
        sys.exit(5)
    except Exception as e:
        logging.log(logging.CRITICAL, e, exc_info=True)
        sys.exit(2)
