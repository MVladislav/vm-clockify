"""LANDWEHR."""

import logging
import sys

import click

from vm_clockify.service.api_landwehr_service import ApiLandwehrService
from vm_clockify.utils.utils_helper import Context, pass_context


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
@click.group()
@pass_context
def cli(ctx: Context):
    """Youtrack-api usage command."""
    ctx.service = ApiLandwehrService()


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
@cli.command()
@click.option("-y", "--year", type=int, help="year to add new time", required=True)
@click.option("-m", "--month", type=int, help="month to add new time", required=True)
@click.option("-d", "--day", type=int, help="day to add new time", required=True)
@click.option("-a", "--auftrag", type=str, help="auftrag where to add the time to", required=True)
@pass_context
def upload(ctx: Context, year: int, month: int, day: int, auftrag: str):
    """Will insert times for default logging into landwehr."""
    try:
        service: ApiLandwehrService = ctx.service
        service.upload(year=year, month=month, day=day, auftrag=auftrag)
    except KeyboardInterrupt as k:
        logging.log(logging.DEBUG, f"process interrupted! ({k})")
        sys.exit(5)
    except Exception as e:
        logging.log(logging.CRITICAL, e, exc_info=True)
        sys.exit(2)
