import logging

import coloredlogs
import verboselogs

from vm_clockify.utils.config import settings


class LogHelper:
    def __init__(
        self,
        logging_verbose: int = settings.LOGGING_VERBOSE,
        logging_level: str = settings.LOGGING_LEVEL,
    ):
        # configure logger for requested verbosity
        if logging_verbose >= 4:
            log_format = "[%(asctime)s,%(msecs)03d] %(name)s[%(process)d] \
                          {%(lineno)-6d: (%(funcName)-30s)} %(levelname)-7s - %(message)s"
        elif logging_verbose >= 3:
            log_format = "[%(filename)-18s/%(module)-15s - %(lineno)-6d: (%(funcName)-30s)]:: %(levelname)-7s - %(message)s"
        elif logging_verbose >= 2 or logging_verbose >= 1:
            log_format = "%(levelname)-7s - %(message)s"
        elif logging_verbose >= 0 or logging_verbose < 0:
            log_format = "%(message)s"
        else:
            log_format = "%(message)s"

        # create a log object from verboselogs
        verboselogs.install()

        for logger_name in [logging.getLogger()] + [logging.getLogger(name) for name in logging.root.manager.loggerDict]:
            for handler in logger_name.handlers:
                logger_name.removeHandler(handler)
            # define log level default
            logger_name.setLevel(logging.getLevelName(logging_level))
            # add colered logs
            coloredlogs.install(
                level=logging.getLevelName(logging_level),
                fmt=log_format,
                logger=logger_name,
            )

            if logging_level == "INFO" and logger_name.name.startswith("httpx"):
                logger_name.setLevel(logging.WARNING)
                logger_name.setLevel(logging.WARNING)
