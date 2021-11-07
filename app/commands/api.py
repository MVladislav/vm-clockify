import logging
import pickle
import sys
from typing import Dict

import click

from ..service.api_service import ApiService, IssueTime
from ..service.api_youtrack_service import ApiYoutrackService
from ..utils.config import (CLOCKIFY_API_ENDPOINT, CLOCKIFY_API_KEY,
                            CLOCKIFY_API_USER_ID, CLOCKIFY_API_WORKSPACE_ID,
                            CLOCKIFY_TMP_FILE, YOUTRACK_API_ENDPOINT,
                            YOUTRACK_API_KEY)
from ..utils.utils import Context, pass_context

default_split_by = ';'

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------


@click.group(invoke_without_command=True)
@click.option('-k', '--key', type=str, help='api key for clockify', default=CLOCKIFY_API_KEY, required=True)
@click.option('-e', '--endpoint', type=str, help='full api endpoint', default=CLOCKIFY_API_ENDPOINT, required=True)
@pass_context
def cli(ctx: Context, key: str, endpoint: str):
    '''
        This is clockify endpoint usage command
    '''
    if ctx.utils.uri_validator(endpoint):
        ctx.api_clockify_key = key
        ctx.api_clockify_endpoint = endpoint
        ctx.service = ApiService(ctx)

        ctx.youtrack_service = ApiYoutrackService(ctx)
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
        This is a test
    '''
    try:
        # logging.log(logging.INFO, f'this is a service call')
        service: ApiService = ctx.service
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
@click.option('-w', '--workspace-id', type=str, help='workspace to use', default=CLOCKIFY_API_WORKSPACE_ID, required=True)
@click.option('-u', '--user-id', type=str, help='user to use', default=CLOCKIFY_API_USER_ID, required=True)
@click.option('-d', '--days-to-subtract', type=int, help='from now until how much days to collect [7]', default=7)
@click.option('-p', '--page-size', type=int, help='how much records should loaded (max 5000) [50]', default=50)
@pass_context
def times(ctx: Context, workspace_id: str, user_id: str, days_to_subtract: int, page_size: int):
    '''
        This api will print you worktime
        HINT: run first user api to get workspace ID and user ID
    '''
    try:
        # logging.log(logging.INFO, f'this is a service call')
        service: ApiService = ctx.service
        service.times(workspaceId=workspace_id, userId=user_id, days_to_subtract=days_to_subtract, page_size=page_size)
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
@click.option('-k', '--key', type=str, help='api key for youtrack', default=YOUTRACK_API_KEY, required=True)
@click.option('-e', '--endpoint', type=str, help='only base url', default=YOUTRACK_API_ENDPOINT, required=True)
@pass_context
def youtrack(ctx: Context, key: str, endpoint: str):
    '''
        This api will insert times collected from clockify into youtrack
        HINT: run clockify times api first
    '''
    try:
        # logging.log(logging.INFO, f'this is a youtrack_service call')
        youtrack_service: ApiYoutrackService = ctx.youtrack_service
        if ctx.utils.uri_validator(endpoint):
            ctx.api_youtrack_key = key
            ctx.api_youtrack_endpint = endpoint

            issues: Dict[str, IssueTime] = None
            with open(CLOCKIFY_TMP_FILE, 'rb') as f:
                issues = pickle.load(f)

            youtrack_service.times(issues=issues)
        else:
            logging.log(logging.WARNING, f'endpoint "{endpoint}" is not a valid url format')
            sys.exit(2)
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
