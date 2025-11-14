from contextlib import AbstractContextManager
from types import TracebackType
from typing import Self

from w3stringsx_lib.utils import ScratchFolder
from w3stringsx_svc.configuration import Configuration


class ScratchFolderService(AbstractContextManager):
    def __init__(self,
        config: Configuration
    ) -> None:
        self.__config = config
        self.__scratch: ScratchFolder | None = None

    def __enter__(self) -> Self:
        self.__ensure_scratch()
        return self
    
    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> bool | None:
        if self.__scratch is not None:
            self.__scratch.__exit__(exc_type, exc_value, traceback)
            self.__scratch = None

    def get(self) -> ScratchFolder:
        return self.__ensure_scratch()


    def __ensure_scratch(self) -> ScratchFolder:
        if self.__scratch is None:
            self.__scratch = ScratchFolder(self.__config.app_dir.get_or_default())
            self.__scratch.__enter__()
        return self.__scratch