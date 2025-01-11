"""LOG HELPER."""

import logging
import sys

import coloredlogs
import verboselogs

from vm_clockify.utils.config import settings


class LogHelper:
    """LogHelper."""

    def __init__(self) -> None:
        """Log Helper init."""
        logger_name_size = self._clean_logs()
        # configure logger for requested verbosity
        log_format: str = "%(message)s"
        if settings.LOGGING_VERBOSE == 2:
            log_format = f"[%(asctime)s] %(levelname)-5s :: %(name)-{logger_name_size}s - %(message)s"
        elif settings.LOGGING_VERBOSE == 1:
            log_format = "[%(asctime)s] - %(message)s"

        self._clean_logs()
        root_logger = logging.getLogger("root")
        root_logger.setLevel(logging.getLevelName(settings.LOGGING_LEVEL))

        # create a log object from verboselogs
        verboselogs.install()
        # add colored logs
        coloredlogs.install(
            level=logging.getLevelName(settings.LOGGING_LEVEL),
            fmt=log_format,
            logger=root_logger,
            stream=sys.stdout,
        )

    def _clean_logs(self) -> int:
        logger_name_size = 4
        for logger_name in [logging.getLogger()] + [logging.getLogger(name) for name in logging.getLogger().manager.loggerDict]:
            for handler in logger_name.handlers:
                logger_name.removeHandler(handler)
            if settings.LOGGING_LEVEL == "INFO" and logger_name.name.startswith("httpx"):
                logger_name.setLevel(logging.WARNING)
            if (logger_name_size := len(logger_name.name)) >= logger_name_size:
                pass
        return logger_name_size + 1
