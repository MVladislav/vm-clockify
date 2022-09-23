import logging
import os

import click

from .utils.config import settings
from .utils.logHelper import LogHelper

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
# Program Header
# Basic user interface header
print(
    r'''    __  ____    ____          ___      __
   /  |/  / |  / / /___ _____/ (_)____/ /___ __   __
  / /|_/ /| | / / / __ `/ __  / / ___/ / __ `/ | / /
 / /  / / | |/ / / /_/ / /_/ / (__  ) / /_/ /| |/ /
/_/  /_/  |___/_/\__,_/\__,_/_/____/_/\__,_/ |___/'''
)
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
        for filename in os.listdir(
            os.path.join(os.path.dirname(__file__), './commands')
        ):
            if filename.endswith('.py') and not filename.startswith('__'):
                rv.append(filename[:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        try:
            mod = __import__(f'vm_clockify.commands.{name}', None, None, ['cli'])
            return mod.cli

        except ImportError as e:
            logging.log(logging.CRITICAL, e)


# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------
CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help'],
    ignore_unknown_options=True,
    auto_envvar_prefix='COMPLEX',
)


@click.command(cls=ComplexCLI, context_settings=CONTEXT_SETTINGS)
@click.option(
    '-v',
    '--verbose',
    count=True,
    help=f'Enables verbose mode [{settings.LOGGING_VERBOSE}]',
    default=settings.LOGGING_VERBOSE,
)
@click.option(
    '-l',
    '--logging-level',
    type=click.Choice(
        [
            'CRITICAL',
            'ERROR',
            'WARNING',
            'SUCCESS',
            'NOTICE',
            'INFO',
            'VERBOSE',
            'DEBUG',
            'SPAM',
        ]
    ),
    help=f'which log level to use [{settings.LOGGING_LEVEL}]',
    default=settings.LOGGING_LEVEL,
)
@click.option(
    '--home',
    type=click.Path(writable=True),
    help=f'home path to save scannes [{settings.BASE_PATH}]',
    default=settings.BASE_PATH,
)
@click.option(
    '-p',
    '--project',
    type=str,
    help=f'project name to store result in [{settings.PROJECT_NAME}]',
    default=settings.PROJECT_NAME,
)
@click.option(
    '-dsp',
    '--disable-split-project',
    is_flag=True,
    help='disable splitting folder struct by project [false]',
)
@click.option(
    '-dsh',
    '--disable-split-host',
    is_flag=True,
    help='disable splitting folder struct by host [false]',
)
@click.option(
    '-pom',
    '--print-only-mode',
    is_flag=True,
    help='command will only printed and not run [false]',
)
@click.option(
    '-s', '--sudo', is_flag=True, help='append sudo for command which need it [false]'
)
@click.option(
    '-t',
    '--terminal-read-mode',
    is_flag=True,
    help='print on subprocess stdout also direct to console [false]',
)
def cli(
    verbose: int,
    logging_level: str,
    home: str,
    project: str,
    disable_split_project: bool,
    disable_split_host: bool,
    print_only_mode: bool,
    sudo: bool,
    terminal_read_mode: bool,
):
    '''
        Welcome to {PROJECT_NAME}

        Example: "{PROJECT_NAME} -vv -p 'nice project' -dsh --home . <COMMAND> [OPTIONS] <COMMAND> [OPTIONS]"
    '''
    # SET: default global values
    settings.LOGGING_VERBOSE = verbose
    settings.LOGGING_LEVEL = logging_level
    settings.BASE_PATH = home
    settings.PROJECT_NAME = project
    settings.DISABLE_SPLIT_PROJECT = disable_split_project
    settings.DISABLE_SPLIT_HOST = disable_split_host
    settings.PRINT_ONLY_MODE = print_only_mode
    settings.USE_SUDO = ['sudo'] if sudo else []
    settings.TERMINAL_READ_MODE = terminal_read_mode
    # INIT: log helper global
    LogHelper(
        logging_verbose=settings.LOGGING_VERBOSE, logging_level=settings.LOGGING_LEVEL
    )
    logging.log(logging.DEBUG, "init start_up...")
    settings.print()
