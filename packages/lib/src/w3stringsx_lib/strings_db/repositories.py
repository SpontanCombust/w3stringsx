from abc import ABC, abstractmethod
from typing import TypeVar, Generic
import sqlite3

from w3stringsx_lib.strings_db import model, queries


_M = TypeVar('_M')
_ID = TypeVar('_ID')

class _Repository(ABC, Generic[_M, _ID]):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._cur: sqlite3.Cursor = conn.cursor()

    @abstractmethod
    def insert(self, obj: _M) -> _M:
        """
        Inserts a new object into table. Returns the created object.
        """
        pass

    @abstractmethod
    def update(self, obj: _M) -> int:
        """
        Updates an existing object. Returns the number of rows updated.
        """
        pass

    @abstractmethod
    def select_all(self) -> list[_M]:
        """
        Returns the list of fetched objects.
        """
        pass

    @abstractmethod
    def select_one(self, id: _ID) -> _M | None:
        """
        Returns fetched object or None if none could be found with that id.
        """
        pass

    @abstractmethod
    def delete(self, id: _ID) -> int:
        """
        Deletes an object with the id from the table. Returns the number of rows deleted.
        """
        pass


class LanguagesRepository(_Repository[model.Languages, int]):
    def insert(self, obj: model.Languages) -> model.Languages:
        raise Exception("Mutative operations not allowed for LANGUAGES table")

        self._cur.execute(
            "INSERT INTO LANGUAGES (ID, LANG, FALLBACK) VALUES (?, ?, ?)",
            (obj.id, obj.lang, obj.fallback),
        )
        self._conn.commit()
        return model.Languages(
            id=obj.id,
            lang=obj.lang,
            fallback=obj.fallback,
        )

    def update(self, obj: model.Languages) -> int:
        raise Exception("Mutative operations not allowed for LANGUAGES table")
    
        self._cur.execute(
            "UPDATE LANGUAGES SET LANG = ?, FALLBACK = ? WHERE ID = ?",
            (obj.lang, obj.fallback, obj.id),
        )
        self._conn.commit()
        return self._cur.rowcount

    def select_all(self) -> list[model.Languages]:
        self._cur.execute("SELECT ID, LANG, FALLBACK FROM LANGUAGES")
        rows = self._cur.fetchall()
        return [
            model.Languages(
                id=r[0],
                lang=r[1],
                fallback=r[2],
            )
            for r in rows
        ]

    def select_one(self, id: int) -> model.Languages | None:
        self._cur.execute("SELECT ID, LANG, FALLBACK FROM LANGUAGES WHERE ID = ?", (id,))
        row = self._cur.fetchone()
        if row:
            return model.Languages(
                id=row[0],
                lang=row[1],
                fallback=row[2],
            )
        return None

    def delete(self, id: int) -> int:
        raise Exception("Mutative operations not allowed for LANGUAGES table")
    
        self._cur.execute("DELETE FROM LANGUAGES WHERE ID = ?", (id,))
        self._conn.commit()
        return self._cur.rowcount


class StringInfoRepository(_Repository[model.StringInfo, int]):
    def insert(self, obj: model.StringInfo) -> model.StringInfo:
        self._cur.execute(
            "INSERT INTO STRING_INFO (STRING_ID, RESOURCE, PROPERTY_NAME, VOICEOVER_NAME, STRING_KEY) VALUES (?, ?, ?, ?, ?)",
            (obj.string_id, obj.resource, obj.property_name, obj.voiceover_name, obj.string_key),
        )
        self._conn.commit()
        return model.StringInfo(
            string_id=obj.string_id,
            resource=obj.resource,
            property_name=obj.property_name,
            voiceover_name=obj.voiceover_name,
            string_key=obj.string_key,
        )

    def update(self, obj: model.StringInfo) -> int:
        self._cur.execute(
            "UPDATE STRING_INFO SET RESOURCE = ?, PROPERTY_NAME = ?, VOICEOVER_NAME = ?, STRING_KEY = ? WHERE STRING_ID = ?",
            (obj.resource, obj.property_name, obj.voiceover_name, obj.string_key, obj.string_id),
        )
        self._conn.commit()
        return self._cur.rowcount

    def select_all(self) -> list[model.StringInfo]:
        self._cur.execute("SELECT STRING_ID, RESOURCE, PROPERTY_NAME, VOICEOVER_NAME, STRING_KEY FROM STRING_INFO")
        rows = self._cur.fetchall()
        return [
            model.StringInfo(
                string_id=r[0],
                resource=r[1],
                property_name=r[2],
                voiceover_name=r[3],
                string_key=r[4],
            )
            for r in rows
        ]

    def select_one(self, id: int) -> model.StringInfo | None:
        self._cur.execute("SELECT STRING_ID, RESOURCE, PROPERTY_NAME, VOICEOVER_NAME, STRING_KEY FROM STRING_INFO WHERE STRING_ID = ?", (id,))
        row = self._cur.fetchone()
        if row:
            return model.StringInfo(
                string_id=row[0],
                resource=row[1],
                property_name=row[2],
                voiceover_name=row[3],
                string_key=row[4],
            )
        return None

    def delete(self, id: int) -> int:
        self._cur.execute("DELETE FROM STRING_INFO WHERE STRING_ID = ?", (id,))
        self._conn.commit()
        return self._cur.rowcount


class StringsRepository(_Repository[model.Strings, tuple[int, int, int]]):
    def insert(self, obj: model.Strings) -> model.Strings:
        self._cur.execute(
            "INSERT INTO STRINGS (STRING_ID, LANG, VERSION, TEXT) VALUES (?, ?, ?, ?)",
            (obj.string_id, obj.lang, obj.version, obj.text),
        )
        self._conn.commit()
        return model.Strings(
            string_id=obj.string_id,
            lang=obj.lang,
            version=obj.version,
            text=obj.text,
        )

    def update(self, obj: model.Strings) -> int:
        self._cur.execute(
            "UPDATE STRINGS SET TEXT = ? WHERE STRING_ID = ? AND LANG = ? AND VERSION = ?",
            (obj.text, obj.string_id, obj.lang, obj.version),
        )
        self._conn.commit()
        return self._cur.rowcount

    def select_all(self) -> list[model.Strings]:
        self._cur.execute("SELECT STRING_ID, LANG, VERSION, TEXT FROM STRINGS")
        rows = self._cur.fetchall()
        return [
            model.Strings(
                string_id=r[0],
                lang=r[1],
                version=r[2],
                text=r[3],
            )
            for r in rows
        ]

    def select_one(self, id: tuple[int, int, int]) -> model.Strings | None:
        string_id, lang, version = id
        self._cur.execute("SELECT STRING_ID, LANG, VERSION, TEXT FROM STRINGS WHERE STRING_ID = ? AND LANG = ? AND VERSION = ?", (string_id, lang, version))
        row = self._cur.fetchone()
        if row:
            return model.Strings(
                string_id=row[0],
                lang=row[1],
                version=row[2],
                text=row[3],
            )
        return None

    def delete(self, id: tuple[int, int, int]) -> int:
        string_id, lang, version = id
        self._cur.execute("DELETE FROM STRINGS WHERE STRING_ID = ? AND LANG = ? AND VERSION = ?", (string_id, lang, version))
        self._conn.commit()
        return self._cur.rowcount
    

    def select_all_latest_with_info(self, lang: int | None = None) -> list[queries.LatestStringsWithInfo]:
        """
        Select the most recent versions of strings together with string info. 
        If `lang` is not None, only records for that language are selected.
        Uses the LATEST_STRINGS_WITH_INFO_NEW view.
        """
        sql = (
            "SELECT STRING_ID, LANG, VERSION, TEXT, RESOURCE, PROPERTY_NAME, VOICEOVER_NAME, STRING_KEY "
            "FROM LATEST_STRINGS_WITH_INFO_NEW"
        )
        params: tuple = ()
        if lang is not None:
            sql += " WHERE LANG = ?"
            params = (lang,)

        self._cur.execute(sql, params)
        rows = self._cur.fetchall()

        return [
            queries.LatestStringsWithInfo(
                string_id=r[0],
                lang=r[1],
                version=r[2],
                text=r[3],
                resource=r[4],
                property_name=r[5],
                voiceover_name=r[6],
                string_key=r[7],
            )
            for r in rows
        ]

    def select_all_latest_with_info_short(self, lang: int | None = None) -> list[queries.LatestStringsWithInfoShort]:
        """
        Select the most recent versions of strings with a reduced set of info fields.
        If `lang` is not None, only records for that language are selected.
        Uses the LATEST_STRINGS_WITH_INFO_NEW view.
        """
        sql = (
            "SELECT STRING_ID, LANG, STRING_KEY, TEXT "
            "FROM LATEST_STRINGS_WITH_INFO_NEW"
        )
        params: tuple = ()
        if lang is not None:
            sql += " WHERE LANG = ?"
            params = (lang,)

        self._cur.execute(sql, params)
        rows = self._cur.fetchall()

        return [
            queries.LatestStringsWithInfoShort(
                string_id=r[0],
                lang=r[1],
                string_key=r[2],
                text=r[3],
            )
            for r in rows
        ]