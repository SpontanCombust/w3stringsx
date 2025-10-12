from __future__ import annotations
import os
from typing import Self, Protocol

from w3stringsx_lib.logging import get_logger
from w3stringsx_svc.configuration import Configuration


logger = get_logger()


class W3StringsEncoderLocator:
    def __init__(self):
        self.handlers: list[W3StringsEncoderLocatorHandler] = []

    def with_handler(self, fallback_handler: W3StringsEncoderLocatorHandler):
        self.handlers.append(fallback_handler)
        return self

    def find(self) -> str | None:
        exe_path: str | None = None
        for handler in self.handlers:
            exe_path = handler.find()
            if exe_path is not None:
                break

        if exe_path is not None:
            logger.info('Found w3strings encoder: %s', exe_path)
            return exe_path
        else:
            logger.info('w3strings encoder could not be found')
            return None

    
class W3StringsEncoderLocatorHandler(Protocol):
    def find(self) -> str | None:
        raise NotImplementedError()

class AppDirW3StringsEncoderLocatorHandler(W3StringsEncoderLocatorHandler):
    def __init__(self, config: Configuration):
        self.app_dir: str = config.app_dir.get_required()

    def find(self) -> str | None:
        logger.info('Looking for w3strings encoder in w3stringsx\'s directory...')

        exe_path = os.path.join(self.app_dir, 'w3strings.exe')
        if os.path.exists(exe_path):
            return exe_path
        
        return None

class PathEnvW3stringsEncoderLocatorHandler(W3StringsEncoderLocatorHandler):
    def find(self) -> str | None:
        logger.info('Looking for w3strings encoder using PATH environment variable...')

        for path in os.environ["PATH"].split(';'):
            exe_path = os.path.join(path, 'w3strings.exe')
            if os.path.exists(exe_path):
                return exe_path
        
        return None

class FromConfigW3stringsEncoderLocatorHandler(W3StringsEncoderLocatorHandler):
    def __init__(self, config: Configuration):
        self.encoder_path: str | None = config.w3strings_encoder_path.get()

    def find(self) -> str | None:
        logger.info('Looking for w3strings encoder using configuration file...')

        if self.encoder_path is not None:
            if os.path.exists(self.encoder_path):
                return self.encoder_path
            else:
                logger.warning('w3strings encoder path set in the configuration file is invalid')
        
        return None
