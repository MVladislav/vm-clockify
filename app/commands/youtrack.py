import logging
import os
import pickle
import sys
from typing import Dict

import click

from ..service.api_clockify_service import IssueTime
from ..service.api_youtrack_service import ApiYoutrackService
from ..utils.config import settings
from ..utils.utilsFolderHelper import create_service_folder
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
    help=f'api key for youtrack [{settings.YOUTRACK_API_KEY}]',
    default=settings.YOUTRACK_API_KEY,
    required=True,
)
@click.option(
    '-e',
    '--endpoint',
    type=str,
    help=f'only base url [{settings.YOUTRACK_API_ENDPOINT}]',
    default=settings.YOUTRACK_API_ENDPOINT,
    required=True,
)
@pass_context
def cli(ctx: Context, key: str, endpoint: str):
    '''
        This is youtrack-api usage command
    '''
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
    '''
        This api will insert times collected from clockify into youtrack
        HINT: run clockify times api first
    '''
    try:
        service: ApiYoutrackService = ctx.service
        issues: Dict[str, IssueTime] = {}
        with open(f'{create_service_folder()}/{settings.CLOCKIFY_TMP_FILE}', 'rb') as f:
            issues = pickle.load(f)
        service.times(issues=issues)
        if os.path.exists(f'{create_service_folder()}/{settings.CLOCKIFY_TMP_FILE}'):
            os.remove(f'{create_service_folder()}/{settings.CLOCKIFY_TMP_FILE}')
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
