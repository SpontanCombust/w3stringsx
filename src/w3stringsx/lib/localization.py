from __future__ import annotations
from functools import total_ordering 


__all__ = [
    "ALL_LANGS",
    "ALL_LANGS_META_MAP",
    "StringId", 
    "StringIdSpace",
    "StringIdSpaceIterator"
]


ALL_LANGS: list[str] = [
    'ar', 
    'br', 
    'cn', 
    'cz', 
    'de', 
    'en', 
    'es', 
    'esmx', 
    'fr', 
    'hu', 
    'it', 
    'jp', 
    'kr', 
    'pl', 
    'ru', 
    'tr', 
    'zh'
]

ALL_LANGS_META_MAP: dict[str, str] = {
    'ar':   'cleartext',
    'br':   'cleartext',
    'cn':   'cleartext',
    'cz':   'cz',
    'de':   'de',
    'en':   'en',
    'es':   'es',
    'esmx': 'cleartext',
    'fr':   'fr',
    'hu':   'hu',
    'it':   'it',
    'jp':   'jp',
    'kr':   'cleartext',
    'pl':   'pl',
    'ru':   'ru',
    'tr':   'cleartext',
    'zh':   'zh',
}


"""
An approximate number with a good amount of headspace.
Mod ID ranges should be WAAAAAY bigger than that anyways.
"""
_VANILLA_STRING_ID_SPACE_END = 1300000
_LEGACY_MOD_STRING_ID_SPACE_START = 2110000000
_LEGACY_MOD_STRING_ID_SPACE_END = 2120000000
_MODERN_MOD_STRING_ID_SPACE_START = 1000000000
_MIN_MOD_STRING_ID = _MODERN_MOD_STRING_ID_SPACE_START

@total_ordering
class StringId:
    id_num: int

    def __init__(self, id_num: int):
        self.id_num = id_num

    def __eq__(self, value: object) -> bool:
        if isinstance(value, StringId):
            return self.id_num == value.id_num
        else:
            return False
    
    def __lt__(self, value: object) -> bool:
        if isinstance(value, StringId):
            return self.id_num < value.id_num
        else:
            return False

    def __add__(self, x: int) -> StringId:
        return StringId(self.id_num + 1)


    def is_vanilla(self) -> bool:
        return self.id_num <= _VANILLA_STRING_ID_SPACE_END

    def is_modded(self) -> bool:
        return self.id_num >= _MIN_MOD_STRING_ID

    def is_legacy_modded(self) -> bool:
        return self.id_num >= _LEGACY_MOD_STRING_ID_SPACE_START and self.id_num <= _LEGACY_MOD_STRING_ID_SPACE_END
    
    def is_modern_modded(self) -> bool:
        return self.id_num >= _MODERN_MOD_STRING_ID_SPACE_START

    def mod_id(self) -> int | None:
        if self.is_vanilla():
            return None
        elif self.is_legacy_modded():
            return (self.id_num - _LEGACY_MOD_STRING_ID_SPACE_START) // 1000
        else:
            return (self.id_num - _MODERN_MOD_STRING_ID_SPACE_START) // 10000
        
    def id_space(self) -> StringIdSpace:
        mod_id = self.mod_id()
        if mod_id is None:
            return StringIdSpace.vanilla()
        elif self.is_legacy_modded():
            return StringIdSpace.legacy_modded(mod_id)
        else:
            return StringIdSpace.modern_modded(mod_id)
        
class StringIdSpace:
    _id_range: range

    def __init__(self, id_range: range) -> None:
        self._id_range = id_range

    def __eq__(self, value: object) -> bool:
        if isinstance(value, StringIdSpace):
            return self._id_range == value._id_range
        else:
            return False
        
    def __hash__(self) -> int:
        return self._id_range.__hash__()
    
    def __iter__(self) -> StringIdSpaceIterator:
        return iter(StringIdSpaceIterator(self))
        

    @staticmethod
    def vanilla() -> StringIdSpace:
        return StringIdSpace(range(
            0, 
            _VANILLA_STRING_ID_SPACE_END
        ))
    
    @staticmethod
    def legacy_modded(mod_id: int) -> StringIdSpace:
        if not mod_id in range(0, 9999):
            raise Exception(f"Mod ID for a legacy ID space is out of range 0-9999: {mod_id}")
        else:
            return StringIdSpace(range(
                _LEGACY_MOD_STRING_ID_SPACE_START + mod_id * 1000,
                _LEGACY_MOD_STRING_ID_SPACE_START + (mod_id + 1) * 1000
            ))
        
    @staticmethod
    def modern_modded(mod_id: int) -> StringIdSpace:
        return StringIdSpace(range(
            _MODERN_MOD_STRING_ID_SPACE_START + mod_id * 10000,
            _MODERN_MOD_STRING_ID_SPACE_START + (mod_id + 1) * 10000
        ))


    @property
    def start(self) -> StringId:
        return StringId(self._id_range.start)
    
    @property
    def stop(self) -> StringId:
        return StringId(self._id_range.stop)
    

    def is_vanilla(self) -> bool:
        return self._id_range.stop <= _VANILLA_STRING_ID_SPACE_END
    
    def is_modded(self) -> bool:
        return self._id_range.start >= _MIN_MOD_STRING_ID
    
    def is_legacy_modded(self) -> bool:
        return self._id_range.start >= _MIN_MOD_STRING_ID
    
    def mod_id(self) -> int | None:
        return self.start.mod_id()


class StringIdSpaceIterator:
    id_space: StringIdSpace
    current_id: StringId

    def __init__(self, id_space: StringIdSpace) -> None:
        self.id_space = id_space
        self.current_id = self.id_space.start

    def __iter__(self) -> StringIdSpaceIterator:
        self.current_id = self.id_space.start
        return self
    
    def __next__(self) -> StringId:
        if self.current_id < self.id_space.stop:
            id = self.current_id
            self.current_id = self.current_id + 1
            return id
        else:
            raise StopIteration
        
    def advance_to(self, id: StringId) -> StringIdSpaceIterator:
        if id >= self.current_id and id < self.id_space.stop:
            self.current_id = id
            return self
        else:
            raise Exception("ID cannot be advanced to %d for this iterator" % id.id_num)