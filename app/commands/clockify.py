import logging
import sys

import click

from ..service.api_clockify_service import ApiClockifyService
from ..utils.config import (CLOCKIFY_API_ENDPOINT, CLOCKIFY_API_KEY,
                            CLOCKIFY_API_USER_ID, CLOCKIFY_API_WORKSPACE_ID)
from ..utils.utils import Context, pass_context

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------


@click.group(invoke_without_command=True)
@click.option('-k', '--key', type=str,
              help=f'api key for clockify [{CLOCKIFY_API_KEY}]', default=CLOCKIFY_API_KEY, required=True)
@click.option('-e', '--endpoint', type=str,
              help=f'full api endpoint [{CLOCKIFY_API_ENDPOINT}]', default=CLOCKIFY_API_ENDPOINT, required=True)
@pass_context
def cli(ctx: Context, key: str, endpoint: str):
    '''
        This is clockify api usage command
    '''
    if ctx.utils is not None:
        if ctx.utils.uri_validator(endpoint):
            ctx.api_clockify_key = key
            ctx.api_clockify_endpoint = endpoint
            ctx.service = ApiClockifyService(ctx)
        else:
            logging.log(logging.WARNING, f'endpoint "{endpoint}" is not a valid url format')
            sys.exit(2)
    else:
        logging.log(logging.ERROR, 'utils are not set')
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
@click.option('-w', '--workspace-id', type=str,
              help=f'workspace to use [{CLOCKIFY_API_WORKSPACE_ID}]', default=CLOCKIFY_API_WORKSPACE_ID, required=True)
@click.option('-u', '--user-id', type=str,
              help=f'user to use [{CLOCKIFY_API_USER_ID}]', default=CLOCKIFY_API_USER_ID, required=True)
@click.option('-d', '--days-to-subtract', type=int,
              help='from now until how much days to collect [0]', default=0, required=True)
@click.option('-p', '--page-size', type=int,
              help='how much records should loaded (max 5000) [50]', default=50, required=True)
@click.option('-sp', '--specific-day', type=str,
              help='specific day to collect (YYYY-MM-DD) [None]', default=None)
@pass_context
def times(ctx: Context, workspace_id: str, user_id: str, days_to_subtract: int, page_size: int, specific_day: str):
    '''
        This api will print you worktime
        HINT: run first user-api to get workspace ID and user ID
    '''
    try:
        service: ApiClockifyService = ctx.service
        service.times(workspaceId=workspace_id, userId=user_id, days_to_subtract=days_to_subtract,
                      page_size=page_size, specific_day=specific_day)
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
