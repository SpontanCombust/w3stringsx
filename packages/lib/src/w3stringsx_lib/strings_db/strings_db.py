from contextlib import AbstractContextManager
import sqlite3
from types import TracebackType
from typing import Self

from w3stringsx_lib.strings_db.schema import SCHEMA
from w3stringsx_lib.strings_db.repositories import LanguagesRepository, StringInfoRepository, StringsRepository


class StringsDb(AbstractContextManager):
    def __init__(self, conn_string: str) -> None:
        self.conn_string = conn_string
        self._conn: sqlite3.Connection | None = None

    def __enter__(self) -> Self:
        if self._conn:
            self._conn.close()
        self._conn = sqlite3.connect(self.conn_string)
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None):
        if self._conn:
            self._conn.close()


    def bootstrap(self):
        if self._conn is None:
            raise sqlite3.DatabaseError()

        self._conn.executescript(SCHEMA)

    def languages_repository(self):
        if self._conn is None:
            raise sqlite3.DatabaseError()
        
        return LanguagesRepository(self._conn)
    
    def string_info_repository(self):
        if self._conn is None:
            raise sqlite3.DatabaseError()
        
        return StringInfoRepository(self._conn)
    
    def strings_repository(self):
        if self._conn is None:
            raise sqlite3.DatabaseError()
        
        return StringsRepository(self._conn)