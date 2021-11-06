import logging
import sys

import click

from ..service.api_service import ApiService
from ..utils.config import (CLOCKIFY_API_ENDPOINT, CLOCKIFY_API_KEY,
                            CLOCKIFY_API_USER_ID, CLOCKIFY_API_WORKSPACE_ID)
from ..utils.utils import Context, pass_context

default_split_by = ';'

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------


@click.group(invoke_without_command=True)
@click.option('-k', '--api-key', type=str, help='api key for clockify', default=CLOCKIFY_API_KEY, required=True)
@click.option('-e', '--api-endpoint', type=str, help='api endpint', default=CLOCKIFY_API_ENDPOINT, required=True)
@pass_context
def cli(ctx: Context, api_key: str, api_endpoint: str):
    '''
        This is clockify endpoint usage command
    '''
    if ctx.utils.uri_validator(api_endpoint):
        if api_endpoint.endswith('/'):
            api_endpoint = api_endpoint[0:-1]

        ctx.api_key = api_key
        ctx.api_endpoint = api_endpoint
        ctx.service = ApiService(ctx)
    else:
        logging.log(logging.WARNING, f'endpoint "{api_endpoint}" is not a valid url format')
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
    service: ApiService = ctx.service
    try:
        # logging.log(logging.INFO, f'this is a service call')
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
    service: ApiService = ctx.service
    try:
        # logging.log(logging.INFO, f'this is a service call')
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
