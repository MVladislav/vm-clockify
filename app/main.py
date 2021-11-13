import logging
import os

import click

from .utils.config import (BASE_PATH, LOGGING_LEVEL, LOGGING_VERBOSE,
                           PROJECT_NAME, VERSION)
from .utils.logHelper import LogHelper
from .utils.utils import Context, Utils, pass_context

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------

# Program Header
# Basic user interface header
print(r'''    __  ____    ____          ___      __
   /  |/  / |  / / /___ _____/ (_)____/ /___ __   __
  / /|_/ /| | / / / __ `/ __  / / ___/ / __ `/ | / /
 / /  / / | |/ / / /_/ / /_/ / (__  ) / /_/ /| |/ /
/_/  /_/  |___/_/\__,_/\__,_/_/____/_/\__,_/ |___/''')
print('**************** 4D 56 6C 61 64 69 73 6C 61 76 *****************')
print('****************************************************************')
print('* Copyright of MVladislav, 2021                                *')
print('* https://mvladislav.online                                    *')
print('* https://github.com/MVladislav                                *')
print('****************************************************************')
print()


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------


class ComplexCLI(click.MultiCommand):
    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(os.path.join(os.path.dirname(__file__), './commands')):
            if filename.endswith('.py') and not filename.startswith('__'):
                rv.append(filename[:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        try:
            mod = __import__(f'app.commands.{name}', None, None, ['cli'])
            return mod.cli
        except ImportError as e:
            logging.log(logging.CRITICAL, e)


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'], ignore_unknown_options=True, auto_envvar_prefix='COMPLEX')


@click.command(cls=ComplexCLI, context_settings=CONTEXT_SETTINGS)
@click.version_option(VERSION)
@click.option('-v', '--verbose', count=True, help=f'Enables verbose mode [{LOGGING_VERBOSE}]', default=LOGGING_VERBOSE)
@click.option('--home', type=click.Path(writable=True), help=f'home path to save scannes [{BASE_PATH}]', default=BASE_PATH)
@click.option('-p', '--project', type=str, help=f'project name to store result in [{PROJECT_NAME}]', default=PROJECT_NAME)
@click.option('-dsp', '--disable-split-project', is_flag=True, help='disable splitting folder struct by project [false]')
@click.option('-dsh', '--disable-split-host', is_flag=True, help='disable splitting folder struct by host [false]')
@click.option('-pom', '--print-only-mode', is_flag=True, help='command will only printed and not run [false]')
@pass_context
def cli(ctx: Context, verbose: int, home: str, project: str,
        disable_split_project: bool, disable_split_host: bool, print_only_mode: bool):
    '''
        Welcome to {PROJECT_NAME}

        Example: "{PROJECT_NAME} -vv -p 'nice project' -dsh --home . <COMMAND> [OPTIONS] <COMMAND> [OPTIONS]"
    '''

    # INIT: log helper global
    LogHelper(logging_verbose=verbose, logging_level=LOGGING_LEVEL)

    logging.log(logging.DEBUG, 'init start_up...')

    # INIT: utils defaults to use ctx global
    ctx.utils = Utils(ctx)

    # SET: default global values
    ctx.project = project
    ctx.base_path = home
    ctx.disable_split_project = disable_split_project
    ctx.disable_split_host = disable_split_host
    ctx.print_only_mode = print_only_mode

    ctx.utils.update(ctx=ctx)
