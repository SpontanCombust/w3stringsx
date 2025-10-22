import os
from typing import Any, Callable, Self


_FileHandler = Callable[..., Any]

class FileTypeRelay:
    def __init__(self) -> None:
        self.__dir_handler: _FileHandler | None = None
        self.__file_handlers: dict[str, _FileHandler] = dict()

    def register_dir_handler(self, handler: _FileHandler) -> Self:
        self.__dir_handler = handler
        return self
    
    def register_file_handler(self, file_exts: list[str], handler: _FileHandler) -> Self:
        for ext in file_exts:
            self.__file_handlers[ext.strip('.')] = handler
        return self
    
    def relay_for_path(self, path: str, *args: Any) -> Any:
        if not os.path.exists(path):
            raise FileNotFoundError()

        if os.path.isdir(path) and self.__dir_handler is not None:
            return self.__dir_handler(*args)
        else:
            _, ext = os.path.splitext(path)
            try:
                handler = self.__file_handlers[ext.strip('.')]
                return handler(*args)
            except KeyError:
                raise Exception('File type "%s" does not have a registered handler' % ext)