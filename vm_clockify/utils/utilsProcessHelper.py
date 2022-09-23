
import logging
import random
import sys
import time
from io import BufferedReader
from subprocess import PIPE, Popen
from typing import IO, Any, List, Tuple, Union

import verboselogs
from progress.spinner import PixelSpinner

from vm_clockify.utils.config import settings
from vm_clockify.utils.defaultLogBanner import log_runBanner
from vm_clockify.utils.utilsHelper import is_tool, prompt_sudo


# ------------------------------------------------------------------------------
#
# command exec - helper
#
# ------------------------------------------------------------------------------
def run_command_endless(command_list=[]) -> None:
    sub_p: Union[Popen[bytes], None] = None
    is_running = True
    try:
        index_to_check = 0
        index_to_check = 1 if command_list[index_to_check] == "sudo" else index_to_check
        # if sudo is in command, first check into root
        if index_to_check == 1:
            if not prompt_sudo():
                sys.exit(4)
        logging.log(verboselogs.NOTICE, " ".join(command_list))
        if is_tool(command_list[index_to_check]):
            with Popen(command_list) as sub_p:
                while is_running:
                    time.sleep(600)
        else:
            logging.log(
                logging.ERROR,
                f'the command "{command_list[index_to_check]}", did not exist',
            )
    except (SystemExit, KeyboardInterrupt) as k:
        logging.log(logging.WARNING, f"process interupted! ({k})")
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


def run_command(
    command_list: List[str] = [], input_value: Union[str, None] = None
) -> Tuple[Union[str, None], Union[str, None], bool]:
    sub_std_res: Union[str, None] = None
    sub_err_res: Union[str, None] = None
    is_interrupted: bool = False
    if not settings.PRINT_ONLY_MODE:
        try:
            sub_std: Union[bytes, str, None] = None
            sub_err: Union[bytes, str, None] = None
            index_to_check = 0
            index_to_check = 1 if command_list[
                index_to_check
            ] == "sudo" else index_to_check
            # if sudo is in command, first check into root
            if index_to_check == 1:
                if not prompt_sudo():
                    sys.exit(4)
            if is_tool(command_list[index_to_check]):
                if input_value is None:
                    # , start_new_session=True
                    with Popen(command_list, stdout=PIPE, stderr=PIPE) as sub_p:
                        sub_std, sub_err, is_interrupted = subprocess_handler(
                            sub_p=sub_p,
                            input_value=input_value,
                            command=command_list[index_to_check],
                        )
                else:
                    with Popen(
                        command_list, stdout=PIPE, stderr=PIPE, stdin=PIPE
                    ) as sub_p:
                        sub_std, sub_err, is_interrupted = subprocess_handler(
                            sub_p=sub_p,
                            input_value=input_value,
                            command=command_list[index_to_check],
                        )
            else:
                logging.log(
                    logging.ERROR,
                    f'the command "{command_list[index_to_check]}", did not exist',
                )
                sub_err = b"MISSING_COMMAND"
            if sub_std is not None and isinstance(sub_std, bytes):
                sub_std_res = sub_std.decode()
            if sub_err is not None and isinstance(sub_err, bytes) and len(sub_err) > 0:
                sub_err_res = sub_err.decode()
                logging.log(logging.WARNING, sub_err.split(b"\n"))
        except KeyboardInterrupt as k:
            logging.log(logging.WARNING, f"process interupted! ({k})")
            is_interrupted = True
        except Exception as e:
            logging.log(logging.CRITICAL, e, exc_info=True)
            raise Exception(e)

    return (sub_std_res, sub_err_res, is_interrupted)


runner_text_it_is_running: List[str] = [
    "...yep, still running",
    "...no stress, process still running",
    "...process is aaalive ;)",
    "...we current still processing, please wait ... loooong time :P",
    "...still running bro",
]


def subprocess_handler(
    sub_p: Popen[Any],
    input_value: Union[str, None] = None,
    command: Union[str, None] = None,
) -> Tuple[Union[bytes, None], Union[bytes, None], bool]:
    sub_std: Union[bytes, None] = None
    sub_err: Union[bytes, None] = None
    sub_p_std: Union[IO[bytes], bytes, None] = None
    sub_p_err: Union[IO[bytes], None] = None
    is_interrupted: bool = False
    try:
        runner_init_count: int = 1
        runner_time_check_running: int = 1
        if sub_p.stdin is not None and input_value is not None:
            sub_p.stdin.write(input_value.encode())
            sub_p.stdin.close()
        if sub_p.poll() is None:
            if not settings.TERMINAL_READ_MODE or (
                command is not None and command == "tee"
            ):
                time.sleep(runner_time_check_running)
                with PixelSpinner("Processing... ") as spinner:
                    while sub_p.poll() is None:
                        if runner_init_count % 6 == 0:
                            spinner.message = f"{random.choice(runner_text_it_is_running)} "
                            runner_init_count = 1
                        spinner.next()
                        runner_init_count += 1
                        time.sleep(runner_time_check_running)
                if sub_p.stdout is not None:
                    sub_p_std = sub_p.stdout
            else:
                if sub_p.stdout is not None:
                    logging.log(
                        logging.INFO,
                        "you run in terminal read mode, some function can maybe not print anything and you will see longer no response, please wait ...",
                    )
                    for stdout_line in sub_p.stdout:
                        if stdout_line is not None and len(stdout_line) > 0:
                            if sub_p_std is None:
                                sub_p_std = stdout_line
                            else:
                                sub_p_std += stdout_line
                            logging.log(
                                logging.INFO, stdout_line.decode().replace("\n", "")
                            )
        if sub_p.stderr is not None:
            sub_p_err = sub_p.stderr
    except (SystemExit, KeyboardInterrupt):
        is_interrupted = True
        if not settings.TERMINAL_READ_MODE:
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


def run_command_output_loop(
    msg: str, cmds: List[List[str]] = [], output: bool = True
) -> Union[str, None]:
    """
    run command from list in a loop, and also optional pipe them into each other
    default exec function is "run_command" with different
    """
    cmd_result: Union[str, None] = None
    is_interrupted: bool = False
    try:
        log_runBanner(msg)
        if len(cmds) <= 1:
            output = False
        for cmd in cmds:
            if not is_interrupted or cmd[0] == "tee":
                what_to_run = " ".join(cmd)
                if not settings.PRINT_ONLY_MODE:
                    logging.log(verboselogs.NOTICE, f"{what_to_run}")
                else:
                    logging.log(verboselogs.NOTICE, f"[!POM!] {what_to_run}")
                if output:
                    cmd_result, std_err, is_interrupted = run_command(
                        command_list=cmd, input_value=cmd_result
                    )
                else:
                    cmd_result, std_err, is_interrupted = run_command(command_list=cmd)
                if std_err is not None and std_err == "MISSING_COMMAND":
                    cmd_result = None
                    logging.log(logging.WARNING, "missing command to perform")
                    break

                if cmd_result is not None:
                    if len(cmd_result) > 0:
                        logging.log(verboselogs.SPAM, f"output is:\n{cmd_result}")
                    else:
                        cmd_result = None
                        if output:
                            logging.log(logging.WARNING, "no result available to pipe")
                            break

                elif output:
                    logging.log(logging.WARNING, "no result available to pipe")
                    break

    except KeyboardInterrupt as k:
        logging.log(logging.WARNING, f"process interupted! ({k})")
        raise KeyboardInterrupt(k)

    except Exception as e:
        logging.log(logging.CRITICAL, e, exc_info=True)
        raise Exception(e)

    if is_interrupted and cmd_result is None:
        raise KeyboardInterrupt(
            "interrupted while shell code was running, and no result was collected"
        )

    return cmd_result
