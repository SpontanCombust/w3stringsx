"""
Common logging tooling.
"""

import logging
import os


__all__ = [
    "get_logger",
    "get_log_file_path",
    "init_logger"
]


_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s (%(pathname)s:%(lineno)d)"


class _ColoredTerminalFormatter(logging.Formatter):
    COLOR_RESET = '\033[0m'
    COLOR_YELLOW = '\033[93m'
    COLOR_RED = '\033[91m'

    FORMATS = {
        logging.DEBUG: _LOG_FORMAT,
        logging.INFO: _LOG_FORMAT,
        logging.WARNING: COLOR_YELLOW + _LOG_FORMAT + COLOR_RESET,
        logging.ERROR: COLOR_RED + _LOG_FORMAT + COLOR_RESET,
        logging.CRITICAL: COLOR_RED + _LOG_FORMAT + COLOR_RESET
    }

    def format(self, record: logging.LogRecord):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


_LOG_FILE_NAME = 'w3stringsx.log'
_log_file_path = os.path.join('.', _LOG_FILE_NAME)

def get_logger():
    return logging.getLogger('w3stringsx')

def get_log_file_path():
    return _log_file_path

def init_logger(log_file_dir: str) -> logging.Logger:
    stdio_handler = logging.StreamHandler()
    stdio_handler.setFormatter(_ColoredTerminalFormatter())

    global _log_file_path
    _log_file_path = os.path.join(log_file_dir or os.getcwd(), _LOG_FILE_NAME)
    file_handler = logging.FileHandler(_log_file_path)
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))

    logger = get_logger()
    logger.addHandler(stdio_handler)
    logger.addHandler(file_handler)

    return logger

def set_log_level(log_level: int):
    logger = get_logger()
    logger.setLevel(log_level)
    for handler in logger.handlers:
        handler.setLevel(log_level)

def subscribe_to_logger(handler: logging.Handler, custom: bool = False):
    logger = get_logger()
    if not custom:
        handler.setLevel(logger.level)
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    logger.addHandler(handler)

def unsubscribe_from_logger(handler: logging.Handler):
    logger = get_logger()
    logger.removeHandler(handler)