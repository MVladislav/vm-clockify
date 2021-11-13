import logging
import pickle
import sys
from typing import Dict

import click

from ..service.api_clockify_service import IssueTime
from ..service.api_youtrack_service import ApiYoutrackService
from ..utils.config import (CLOCKIFY_TMP_FILE, YOUTRACK_API_ENDPOINT,
                            YOUTRACK_API_KEY)
from ..utils.utils import Context, pass_context

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------


@click.group(invoke_without_command=True)
@click.option('-k', '--key', type=str,
              help=f'api key for youtrack [{YOUTRACK_API_KEY}]', default=YOUTRACK_API_KEY, required=True)
@click.option('-e', '--endpoint', type=str,
              help=f'only base url [{YOUTRACK_API_ENDPOINT}]', default=YOUTRACK_API_ENDPOINT, required=True)
@pass_context
def cli(ctx: Context, key: str, endpoint: str):
    '''
        This is youtrack-api usage command
    '''
    if ctx.utils is not None:
        if ctx.utils.uri_validator(endpoint):
            ctx.api_youtrack_key = key
            ctx.api_youtrack_endpint = endpoint
            ctx.service = ApiYoutrackService(ctx)
        else:
            logging.log(logging.WARNING, f'endpoint "{endpoint}" is not a valid url format')
            sys.exit(2)
    else:
        logging.log(logging.ERROR, 'utils are not set')
        sys.exit(1)

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------


@cli.command()
@pass_context
def youtrack(ctx: Context):
    '''
        This api will insert times collected from clockify into youtrack
        HINT: run clockify times api first
    '''
    try:
        service: ApiYoutrackService = ctx.service

        issues: Dict[str, IssueTime] = {}
        with open(f'{ctx.utils.create_service_folder()}/{CLOCKIFY_TMP_FILE}', 'rb') as f:
            issues = pickle.load(f)
        service.times(issues=issues)
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
