from __future__ import annotations


__all__ = [
    "ALL_LANGS",
    "ALL_LANGS_META_MAP",
    "StringId"
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
_NEW_MOD_STRING_ID_SPACE_START = 1000000000
_MIN_MOD_STRING_ID = _NEW_MOD_STRING_ID_SPACE_START

def _is_vanilla_string_id(id_num: int) -> bool:
    return id_num <= _VANILLA_STRING_ID_SPACE_END

def _is_modded_string_id(id_num: int) -> bool:
    return id_num >= _MIN_MOD_STRING_ID


class StringId:
    def __init__(self, id_num: int):
        self.id_num = id_num

class ModStringId(StringId):
    def __init__(self, id_num: int):
        super().__init__(id_num)

    def is_legacy(self) -> bool:
        return self.id_num >= _LEGACY_MOD_STRING_ID_SPACE_START and self.id_num <= _LEGACY_MOD_STRING_ID_SPACE_END

    def mod_id(self) -> int:
        if self.is_legacy():
            return (self.id_num - _LEGACY_MOD_STRING_ID_SPACE_START) // 1000
        else:
            return (self.id_num - _NEW_MOD_STRING_ID_SPACE_START) // 10000
        
    # Exclusive range of IDs valid for a mod to which this ID belongs
    def id_space(self) -> range:
        mod_id = self.mod_id()
        if self.is_legacy():
            return range(
                _LEGACY_MOD_STRING_ID_SPACE_START + mod_id * 1000,
                _LEGACY_MOD_STRING_ID_SPACE_START + (mod_id + 1) * 1000
            )
        else:
            return range(
                _NEW_MOD_STRING_ID_SPACE_START + mod_id * 10000,
                _NEW_MOD_STRING_ID_SPACE_START + (mod_id + 1) * 10000
            )

class StringIdParser:
    def parse(self, id_num: int) -> StringId:
        if _is_vanilla_string_id(id_num):
            return StringId(id_num)
        elif _is_modded_string_id(id_num):
            return ModStringId(id_num)
        else:
            raise Exception(
                "ID is not a vanilla nor a valid modded string ID.\n" \
                "Modded string ID should be greater than " + str(_MIN_MOD_STRING_ID) + ".\n" \
                "Currently established string ID space convention can be found explained on the official Witcher 3 discord server:\n" \
                "https://discord.com/channels/597170291021709327/1326868944572907620/1326868944572907620"
            )
    