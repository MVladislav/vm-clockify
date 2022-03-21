import logging
import sys

import click

from ..service.api_clockify_service import ApiClockifyService
from ..utils.config import settings
from ..utils.utilsHelper import Context, pass_context, uri_validator


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
@click.group()
@click.option(
    '-k',
    '--key',
    type=str,
    help=f'api key for clockify [{settings.CLOCKIFY_API_KEY}]',
    default=settings.CLOCKIFY_API_KEY,
    required=True,
)
@click.option(
    '-e',
    '--endpoint',
    type=str,
    help=f'full api endpoint [{settings.CLOCKIFY_API_ENDPOINT}]',
    default=settings.CLOCKIFY_API_ENDPOINT,
    required=True,
)
@pass_context
def cli(ctx: Context, key: str, endpoint: str):
    '''
        This is clockify api usage command
    '''
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
    '''
        This api will return some needed information from user for
        times-api
    '''
    try:
        service: ApiClockifyService = ctx.service
        service.user()
    except KeyboardInterrupt as k:
        logging.log(logging.DEBUG, f'process interupted! ({k})')
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
    '-w',
    '--workspace-id',
    type=str,
    help=f'workspace to use [{settings.CLOCKIFY_API_WORKSPACE_ID}]',
    default=settings.CLOCKIFY_API_WORKSPACE_ID,
    required=True,
)
@click.option(
    '-u',
    '--user-id',
    type=str,
    help=f'user to use [{settings.CLOCKIFY_API_USER_ID}]',
    default=settings.CLOCKIFY_API_USER_ID,
    required=True,
)
@click.option(
    '-d',
    '--days-to-subtract',
    type=int,
    help='from now until how much days to collect [0]',
    default=0,
    required=True,
)
@click.option(
    '-p',
    '--page-size',
    type=int,
    help='how much records should loaded (max 5000) [50]',
    default=50,
    required=True,
)
@click.option(
    '-sp',
    '--specific-day',
    type=str,
    help='specific day to collect (YYYY-MM-DD) [None]',
    default=None,
)
@click.option(
    '-ps',
    '--project-search',
    type=str,
    help='specific project name to filter for [None]',
    default=None,
)
@click.option(
    '-ts',
    '--task-search',
    type=str,
    help='specific task name to filter for [None]',
    default=None,
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
    task_search: str
):
    '''
        This api will print you worktime
        HINT: run first user-api to get workspace ID and user ID
    '''
    try:
        settings.CLOCKIFY_API_WORKSPACE_ID = workspace_id
        settings.CLOCKIFY_API_USER_ID = user_id
        service: ApiClockifyService = ctx.service
        service.times(
            workspaceId=workspace_id,
            userId=user_id,
            days_to_subtract=days_to_subtract,
            page_size=page_size,
            specific_day=specific_day,
            project_name=project_search,
            task_name=task_search,
        )
    except KeyboardInterrupt as k:
        logging.log(logging.DEBUG, f'process interupted! ({k})')
        sys.exit(5)
    except Exception as e:
        logging.log(logging.CRITICAL, e, exc_info=True)
        sys.exit(2)


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
