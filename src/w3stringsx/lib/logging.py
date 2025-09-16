import logging
import os

from w3stringsx import W3STRINGSX_PKG_ROOT


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


def get_logger():
    return logging.getLogger('w3stringsx')

def log_file_path():
    return os.path.join(os.path.dirname(W3STRINGSX_PKG_ROOT), 'w3stringsx.log')

def init_logger(log_level: int):
    stdio_handler = logging.StreamHandler()
    stdio_handler.setLevel(log_level)
    stdio_handler.setFormatter(_ColoredTerminalFormatter())

    file_handler = logging.FileHandler(log_file_path())
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))

    logger = get_logger()
    logger.setLevel(log_level)
    logger.addHandler(stdio_handler)
    logger.addHandler(file_handler)
