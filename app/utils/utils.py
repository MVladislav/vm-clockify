import logging
import os
import random
import re
import socket
import sys
import time
import unicodedata
from io import BufferedReader
from pathlib import Path
from shutil import which
from subprocess import PIPE, Popen, check_call
from typing import IO, Any, Dict, List, Tuple, Union
from urllib.parse import urlparse

import click
import verboselogs
# from libnmap.objects.report import NmapReport
# from libnmap.parser import NmapParser
# from libnmap.process import NmapProcess
from progress.spinner import PixelSpinner
from progressbar import ETA, Bar, Counter, ProgressBar, Timer
from stringcolor import bold

from .config import BASE_PATH, ENV_MODE, LOGGING_LEVEL, PROJECT_NAME
from .defaultLogBanner import log_runBanner
from .locater import Locator

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------


class Context:

    progress: Dict[int, ProgressBar] = {}

    def __init__(self):

        logging.log(logging.DEBUG, 'init context...')

        self.service: Any = None

        self.project: str = PROJECT_NAME
        self.base_path: str = BASE_PATH
        self.home_path: Path = Path.home()

        self.use_sudo: List[str] = []

        self.utils: Utils = Utils(self)

        self.disable_split_project: Union[bool, None] = None
        self.disable_split_host: Union[bool, None] = None
        self.print_only_mode: Union[bool, None] = None
        self.terminal_read_mode: bool = False

        self.logging_verbose: Union[int, None] = None
        self.logging_level: Union[str, None] = None

        # for clockify
        self.api_clockify_key: Union[str, None] = None
        self.api_clockify_endpoint: Union[str, None] = None

        # for youtrack
        self.api_youtrack_key: Union[str, None] = None
        self.api_youtrack_endpint: Union[str, None] = None


pass_context = click.make_pass_decorator(Context, ensure=True)

# ------------------------------------------------------------------------------
#
#
#
# ------------------------------------------------------------------------------


class Utils:

    runner_init_count = 1
    runner_time_check_running = 1
    runner_text_it_is_running = [
        "...yep, still running",
        "...no stress, process still running",
        "...process is aaalive ;)",
        "...we current still processing, please wait ... loooong time :P",
        "...still running bro"
    ]

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def __init__(self, ctx: Context):
        self.update(ctx, is_init=True)

    def update(self, ctx: Context, is_init: bold = False):
        self.ctx = ctx

        if not is_init and LOGGING_LEVEL == logging.getLevelName(logging.DEBUG):
            print()
            print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
            logging.log(logging.DEBUG, f'LOGGING-LEVEL          : {bold(ctx.logging_level)}')
            logging.log(logging.DEBUG, f'LOGGING-VERBOSE        : {bold(ctx.logging_verbose)}')
            logging.log(logging.DEBUG, f'DISABLED SPLIT PROJECT : {bold(self.ctx.disable_split_project)}')
            logging.log(logging.DEBUG, f'DISABLED SPLIT HOST    : {bold(self.ctx.disable_split_host)}')
            logging.log(logging.DEBUG, f'PRINT ONLY MODE        : {bold(self.ctx.print_only_mode)}')
            logging.log(logging.DEBUG, f'PROJECT-PATH           : {bold(self.create_service_path(None))}{bold("/")}')
            logging.log(logging.DEBUG, f'ENV-MODE               : {bold(ENV_MODE)}')
            print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
            print()

    # --------------------------------------------------------------------------
    #
    # path | folder | file - helper
    #
    # --------------------------------------------------------------------------

    def create_folder(self, path: str) -> None:
        '''
            create a folder under giving path
        '''
        Path(path).mkdir(parents=True, exist_ok=True, mode=0o700)

    def get_user_path(self) -> str:
        '''
            returns path to user home
        '''
        return str(Path.home())

    def create_service_folder(self, name: Union[str, None] = None, host: Union[str, None] = None, split_host=None, split_project=None) -> str:
        '''
            creates a folder with name optional host under base path
        '''
        path = self.create_service_path(host=host,
                                        split_host=split_host, split_project=split_project)
        path = f'{path}/{name}' if name is not None else path
        self.create_folder(path)
        logging.log(logging.DEBUG, f'new folder created:: {path}')
        return path

    def create_service_path(self, host: Union[str, None] = None, split_host=None, split_project=None) -> str:
        '''
            creates a path name, will used in call by "create_service_folder"
        '''
        split_host = not self.ctx.disable_split_host if split_host is None else split_host
        split_project = not self.ctx.disable_split_project if split_project is None else split_project

        if split_host and host is not None:
            host = self.slugify(host)
            host = '' if host is None else f'/{host}'
        else:
            host = ''
        if split_project:
            project = '' if self.ctx.project is None else f'/{self.ctx.project}'
        else:
            project = ''

        if self.ctx.base_path[-1] == '/':
            self.ctx.base_path = self.ctx.base_path[:-1]

        return f'{self.ctx.base_path}{project}{host}'

    # --------------------------------------------------------------------------
    #
    # command exec - helper
    #
    # --------------------------------------------------------------------------

    def run_command_endless(self, command_list=[]) -> None:
        sub_p: Union[Popen[bytes], None] = None
        is_running = True
        try:
            index_to_check = 0
            index_to_check = 1 if command_list[index_to_check] == 'sudo' else index_to_check

            # if sudo is in command, first check into root
            if index_to_check == 1:
                if self.prompt_sudo() != 0:
                    sys.exit(4)

            logging.log(verboselogs.NOTICE, ' '.join(command_list))

            if self.is_tool(command_list[index_to_check]):
                with Popen(command_list) as sub_p:
                    while is_running:
                        time.sleep(600)
            else:
                logging.log(logging.ERROR, f'the command "{command_list[index_to_check]}", did not exist')
        except (SystemExit, KeyboardInterrupt) as k:
            logging.log(logging.WARNING, f'process interupted! ({k})')
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)
        is_running = False
        try:
            if sub_p is not None:
                sub_p.terminate()
        except Exception:
            pass
        try:
            if sub_p is not None:
                while sub_p.poll() is None:
                    time.sleep(1)
        except Exception:
            pass

    def run_command(self, command_list: List[str] = [], input_value: Union[str, None] = None
                    ) -> Tuple[Union[str, None], Union[str, None], bool]:
        sub_std_res: Union[str, None] = None
        sub_err_res: Union[str, None] = None

        is_interrupted: bool = False

        if not self.ctx.print_only_mode:
            try:
                sub_std: Union[bytes, str, None] = None
                sub_err: Union[bytes, str, None] = None

                index_to_check = 0
                index_to_check = 1 if command_list[index_to_check] == 'sudo' else index_to_check

                # if sudo is in command, first check into root
                if index_to_check == 1:
                    if self.prompt_sudo() != 0:
                        sys.exit(4)

                if self.is_tool(command_list[index_to_check]):
                    if input_value is None:
                        # , start_new_session=True
                        with Popen(command_list, stdout=PIPE, stderr=PIPE) as sub_p:
                            sub_std, sub_err, is_interrupted = self.subprocess_handler(
                                sub_p=sub_p, input_value=input_value, command=command_list[index_to_check])
                    else:
                        with Popen(command_list, stdout=PIPE, stderr=PIPE, stdin=PIPE) as sub_p:
                            sub_std, sub_err, is_interrupted = self.subprocess_handler(
                                sub_p=sub_p, input_value=input_value, command=command_list[index_to_check])
                else:
                    logging.log(logging.ERROR, f'the command "{command_list[index_to_check]}", did not exist')
                    sub_err = b"MISSING_COMMAND"

                if sub_std is not None and isinstance(sub_std, bytes):
                    sub_std_res = sub_std.decode()
                if sub_err is not None and isinstance(sub_err, bytes) and len(sub_err) > 0:
                    sub_err_res = sub_err.decode()
                    logging.log(logging.ERROR, sub_err.split(b'\n'))

            except KeyboardInterrupt as k:
                logging.log(logging.WARNING, f'process interupted! ({k})')
                is_interrupted = True
            except Exception as e:
                logging.log(logging.CRITICAL, e, exc_info=True)
        return (sub_std_res, sub_err_res, is_interrupted)

    def subprocess_handler(self, sub_p: Popen[Any], input_value: Union[str, None] = None,
                           command: Union[str, None] = None
                           ) -> Tuple[Union[bytes, None], Union[bytes, None], bool]:
        sub_std: Union[bytes, None] = None
        sub_err: Union[bytes, None] = None

        sub_p_std: Union[IO[bytes], bytes, None] = None
        sub_p_err: Union[IO[bytes], None] = None

        is_interrupted: bool = False

        try:
            if sub_p.stdin is not None and input_value is not None:
                sub_p.stdin.write(input_value.encode())
                sub_p.stdin.close()

            if sub_p.poll() is None:
                if not self.ctx.terminal_read_mode or (command is not None and command == 'tee'):
                    time.sleep(self.runner_time_check_running)
                    with PixelSpinner('Processing... ') as spinner:
                        while sub_p.poll() is None:
                            if self.runner_init_count % 6 == 0:
                                spinner.message = f'{random.choice(self.runner_text_it_is_running)} '
                                self.runner_init_count = 1
                            spinner.next()
                            self.runner_init_count += 1
                            time.sleep(self.runner_time_check_running)

                    if sub_p.stdout is not None:
                        sub_p_std = sub_p.stdout
                else:
                    if sub_p.stdout is not None:
                        logging.log(
                            logging.INFO, 'you run in terminal read mode, some function can maybe not print anything and you will see longer no response, please wait ...')
                        for stdout_line in sub_p.stdout:
                            if stdout_line is not None and len(stdout_line) > 0:
                                if sub_p_std is None:
                                    sub_p_std = stdout_line
                                else:
                                    sub_p_std += stdout_line
                                logging.log(logging.INFO, stdout_line.decode().replace('\n', ''))
            if sub_p.stderr is not None:
                sub_p_err = sub_p.stderr
        except (SystemExit, KeyboardInterrupt):
            is_interrupted = True
            if not self.ctx.terminal_read_mode:
                if sub_p.stdout is not None:
                    sub_p_std = sub_p.stdout
            if sub_p.stderr is not None:
                sub_p_err = sub_p.stderr
            try:
                sub_p.kill()
            except Exception:
                pass

        if isinstance(sub_p_std, bytes):
            sub_std = sub_p_std
        if isinstance(sub_p_std, BufferedReader):
            sub_std = sub_p_std.read()
        if isinstance(sub_p_err, BufferedReader):
            sub_err = sub_p_err.read()
        return (sub_std, sub_err, is_interrupted)

    def is_tool(self, name: str) -> bool:
        '''
            Check whether `name` is on PATH and marked as executable.
        '''
        return which(name) is not None

    def run_command_output_loop(self, msg: str, cmds: List[List[str]] = [], output: bool = True) -> Union[str, None]:
        '''
            run command from list in a loop, and also optional pipe them into each other
            default exec function is "run_command" with different
        '''
        cmd_result: Union[str, None] = None
        is_interrupted: bool = False
        try:
            log_runBanner(msg)
            if len(cmds) <= 1:
                output = False
            for cmd in cmds:
                if not is_interrupted or cmd[0] == 'tee':
                    logging.log(verboselogs.NOTICE, ' '.join(cmd))
                    if output:
                        cmd_result, std_err, is_interrupted = self.run_command(
                            command_list=cmd, input_value=cmd_result)
                    else:
                        cmd_result, std_err, is_interrupted = self.run_command(command_list=cmd)
                    if std_err is not None and std_err == "MISSING_COMMAND":
                        cmd_result = None
                        break
                    if cmd_result is not None:
                        if len(cmd_result) > 0:
                            logging.log(verboselogs.SPAM, f'output is:\n{cmd_result}')
                        else:
                            cmd_result = None
                            if output:
                                logging.log(logging.WARNING, 'no result available to pipe')
                                break
                    elif output:
                        logging.log(logging.WARNING, 'no result available to pipe')
                        break
        except KeyboardInterrupt as k:
            logging.log(logging.WARNING, f'process interupted! ({k})')
            raise KeyboardInterrupt
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)
        if is_interrupted and cmd_result is None:
            raise KeyboardInterrupt
        return cmd_result

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def group(self, flat: List[Any], size: int) -> List[Any]:
        '''
            group list a flat list into a matrix of "size"
        '''
        return [flat[i:i+size] for i in range(0, len(flat), size)]

    def normalize_caseless(self, text: str) -> str:
        '''
            lowercase a string, for any unicode
        '''
        return unicodedata.normalize('NFKD', text.casefold())

    def slugify(self, value: Union[str, None], allow_unicode: bool = False) -> Union[str, None]:
        '''
            https://github.com/django/django/blob/main/django/utils/text.py
        '''
        value = str(value)
        if allow_unicode:
            value = unicodedata.normalize('NFKC', value)
        else:
            value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        value = re.sub(r'[^\w\s-]', '', value.lower())
        return re.sub(r'[-\s]+', '-', value).strip('-_')

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def in_sudo_mode(self) -> None:
        '''
            If the user doesn't run the program with super user privileges, don't allow them to continue.
        '''
        if 'SUDO_UID' not in os.environ.keys():
            logging.log(logging.ERROR, 'Try running this program with sudo.')
            sys.exit(1)

    def prompt_sudo(self) -> int:
        try:
            if os.geteuid() != 0:
                msg = "hay [sudo] password for %u: "
                return check_call(f"sudo -v -p '{msg}'", shell=True)
        except Exception:
            pass
        return -1

    def get_ip_address(self) -> Union[str, None]:
        IP = None
        st = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            st.connect(('10.255.255.255', 1))
            IP = st.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            st.close()
        return IP

    def uri_validator(self, url: str) -> Union[str, None]:
        try:
            if url.endswith('/'):
                url = url[:-1]
            result = urlparse(url)
            if all([result.scheme, result.netloc]):
                return url
        except Exception:
            pass
        return None

    def geo(self) -> Union[str, None]:
        '''
            This is a geo test example
        '''
        try:
            return Locator(ctx=self.ctx).check_database()
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)
        return None

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def progress(self, id: int, value: int, description: str = "Processing", maxval: int = 100) -> None:
        try:
            # if self.ctx.progress.get(id) is None:
            #     self.ctx.progress[id] = tqdm(total=maxval, desc=description, colour="#000", leave=False)
            # if self.ctx.progress.get(id) is not None:
            #     bar = self.ctx.progress.get(id)
            #     bar.update(value)

            if self.ctx.progress.get(id) is None:
                self.ctx.progress[id] = ProgressBar(
                    widgets=[description, ' [', Timer(), '] ', Bar(marker='O'), ' [', Counter(
                        format='%(value)02d/%(max_value)d'), ']', ' (', ETA(), ') '],
                    maxval=maxval).start()
            bar_p: ProgressBar = self.ctx.progress.get(id)
            bar_p.update(value=value)
            if value >= maxval:
                print()
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)

    # def nmap_process(self, msg: str, host: str, options: List[str], safe_mode: bool = True) -> NmapReport:
    #     try:
    #         log_runBanner(msg)
    #         logging.log(verboselogs.NOTICE, f'nmap {" ".join(host)} {" ".join(options)}')
    #         if not self.ctx.print_only_mode:
    #             nmap_proc: NmapProcess = NmapProcess(targets=host, options=' '.join(options), safe_mode=safe_mode)
    #             nmap_proc.run_background()
    #             while nmap_proc.is_running():
    #                 self.progress(100, float(nmap_proc.progress))
    #                 time.sleep(0.01)
    #             self.progress(100, 100)
    #             if nmap_proc.stderr is not None:
    #                 if "QUITTING" in nmap_proc.stderr:
    #                     logging.log(logging.CRITICAL, nmap_proc.stderr)
    #                     return None
    #                 logging.log(logging.WARNING, nmap_proc.stderr)
    #             return NmapParser.parse(nmap_proc.stdout)
    #     except Exception as e:
    #         logging.log(logging.CRITICAL, e, exc_info=True)

    # --------------------------------------------------------------------------
    #
    #
    #
    # --------------------------------------------------------------------------

    def define_option_list(self, options: str, default_options: List[Any] = [],
                           options_append: bool = False, default_split_by: str = ',') -> List[Any]:
        '''
            defines a list of option to use in a callable service
            to define how to create this list
            by:
                - create it from a default only
                - create it from params only
                - create it by combine default and params
        '''
        try:
            result: List[Any] = []
            # add options from params
            if options is not None and not options_append:
                result = [options]  # .split(default_split_by)
            # add options from params to existing options
            elif options is not None and options_append:
                result = default_options + [options]  # .split(default_split_by)
            # use existing options
            else:
                result = default_options
            return result
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)
        return []
