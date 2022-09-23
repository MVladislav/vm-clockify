import logging
import sys

import click

from ..service.api_landwehr_service import ApiLandwehrService
from ..utils.utilsHelper import Context, pass_context


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
@click.group()
@pass_context
def cli(ctx: Context):
    '''
        This is youtrack-api usage command
    '''
    ctx.service = ApiLandwehrService()


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
@cli.command()
@click.option('-y', '--year', type=int, help=f'year to add new time', required=True)
@click.option('-m', '--month', type=int, help=f'month to add new time', required=True)
@click.option('-d', '--day', type=int, help=f'day to add new time', required=True)
@click.option('-a', '--auftrag', type=str, help=f'auftrag where to add the time to', required=True)
@pass_context
def upload(ctx: Context, year: int, month: int, day: int, auftrag: str):
    '''
        This api will insert times for default logging into landwehr
    '''
    try:
        service: ApiLandwehrService = ctx.service
        service.upload(year=year, month=month, day=day, auftrag=auftrag)
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
