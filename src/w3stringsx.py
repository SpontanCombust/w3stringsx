from __future__ import annotations
import argparse
from enum import Enum
import io
import os
import re
import shutil
import subprocess
import sys
from typing import Any, Literal, cast
from xml.etree import ElementTree


###############################################################################################################################
# CONSTANTS AND ENUMS
###############################################################################################################################

W3STRINGSX_VERSION = '1.2.0'

ALL_LANGS: list[str] = ['ar', 'br', 'cn', 'cz', 'de', 'en', 'es', 'esmx', 'fr', 'hu', 'it', 'jp', 'kr', 'pl', 'ru', 'tr', 'zh']
ALL_LANGS_META: dict[str, str] = {
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

MOD_ID_RANGE: range = range(2110000000, 2120000000)

BUNDLED_XML_LOCALIZATION_ATTRIBS: dict[str, list[str]] = {
    # gameplay/abilities
    'effect': ['effectNameLocalisationKey_name', 'effectDescriptionLocalisationKey_name'],
    'skill': ['localisationName', 'localisationDescriptionNotAcquired', 'localisationDescription', 'localisationDescriptionLevel2', 'localisationDescriptionLevel3'],
    # gameplay/items
    'item': ['localisation_key_name', 'localisation_key_description'],
    'recipe': ['localisation_key_name']
}

COMMENT_SECTION_MENU = "menu"
COMMENT_SECTION_BUNDLE = "bundle"
COMMENT_SECTION_SCRIPTS = "scripts"

COLOR_NONE = '\033[0m'
COLOR_WARN = '\033[93m'
COLOR_ERROR = '\033[91m'


class InputPathType(Enum):
    UNSUPPORTED         = 0
    W3STRINGS_FILE      = 1
    CSV_FILE            = 2
    XML_FILE            = 3
    WITCHERSCRIPT_FILE  = 4
    DIRECTORY           = 5

    @classmethod
    def from_path(cls, path: str) -> InputPathType:
        if os.path.isdir(path):
            return InputPathType.DIRECTORY
        else:
            _, ext = os.path.splitext(path)
            match ext:
                case '.w3strings':
                    return InputPathType.W3STRINGS_FILE
                case '.csv':
                    return InputPathType.CSV_FILE
                case '.xml':
                    return InputPathType.XML_FILE
                case '.ws' | '.wss':
                    return InputPathType.WITCHERSCRIPT_FILE
                case _:
                    return InputPathType.UNSUPPORTED



###############################################################################################################################
# UTILITIES
###############################################################################################################################

logging_level: int = 3

def log_info(s: str):
    if logging_level >= 3:
        print(f'[INFO] {s}')

def log_warning(s: str):
    if logging_level >= 2:
        print(f'{COLOR_WARN}[WARN] {s}{COLOR_NONE}')

def log_error(s: str):
    if logging_level >= 1:
        print(f'{COLOR_ERROR}[ERROR] {s}{COLOR_NONE}', file=sys.stderr)


# Because encoder ALWAYS puts output in the same directory as input before we are able to move it 
# we first need to create a temporary folder in which we'll execute the commands
# This way no files will be overwritten without user's consent
class ScratchFolder:
    input_copy_path: str # basename should be exactly the same as original input basename 
    folder_path: str

    # Returns path to input that was copied to scratch 
    def __init__(self, input_file: str):
        input_folder, input_basename = os.path.split(input_file)
        self.folder_path = os.path.join(input_folder, '.tmp.w3stringsx')
        if not os.path.exists(self.folder_path):
            log_info(f'Creating scratch folder {self.folder_path}')
            os.mkdir(self.folder_path)

        input_copy = os.path.join(self.folder_path, input_basename)
        shutil.copy(input_file, input_copy)
        
        self.input_copy_path = input_copy

    def __del__(self):
        log_info(f'Removing scratch folder {self.folder_path}')
        shutil.rmtree(self.folder_path)


def lf_to_crlf(file_path: str):
    with io.open(file_path, mode="r+") as f:
        data = f.read()
        data.replace('\n', '\r\n')
        f.seek(0)
        f.write(data)
        f.truncate()


# Returns whether this path that may not exist could point to a file
def maybeisfile(path:str) -> bool:
    return os.path.splitext(path)[1] != ''


def guess_file_encoding(path: str) -> str:
    with io.open(path, mode="rb") as f:
        header = f.read(3)
        if header.startswith(b'\xFF\xFE'):
            return "UTF-16-LE"
        elif header.startswith(b'\xFE\xFF'):
            return "UTF-16-BE"
        elif header.startswith(b'\xEF\xBB\xBF'):
            return "UTF-8-SIG"

    return "UTF-8"


def resolve_output_path(input_path: str, output_path: str, pattern_for_dir: str = '') -> str:
    if not os.path.isdir(output_path) and maybeisfile(output_path):
        return output_path
    
    # if output_path is not a file, it MUST be an existing directory
    
    input_basename = os.path.basename(input_path)

    output_basename: str
    if pattern_for_dir != '':
        output_basename = pattern_for_dir
        if "{stem}" in pattern_for_dir:
            stem = os.path.splitext(input_basename)[0]
            output_basename = output_basename.replace("{stem}", stem)
    else:
        output_basename = input_basename

    return os.path.join(output_path, output_basename)


# also preserve the order of first appearance
def remove_duplicate_keys_and_filter(keys: list[str], search: str) -> list[str]:
    key_set = set[str]()  # using set for fast lookup
    result = list[str]()

    for k in keys:
        if k not in key_set:
            key_set.add(k)
            result.append(k)

    result = list(filter(lambda k: k != "", result))
    if search != "":
        result = list(filter(lambda k: re.search(search, k) is not None, result))

    return result


# set operation, but done to preserve the order of lhs
def key_list_difference(lhs: list[str], rhs: list[str]) -> list[str]:
    rhs_set = set(rhs)
    return [k for k in lhs if k not in rhs_set]


###############################################################################################################################
# ENCODER
###############################################################################################################################

class W3StringsEncoder:
    exe_path: str

    def __init__(self):
        # check script's folder
        self.exe_path = os.path.join(os.path.dirname(__file__), 'w3strings.exe')
        
        if not os.path.exists(self.exe_path):
            # check PATH
            for path in os.environ["PATH"].split(';'):
                encoder_path = os.path.join(path, 'w3strings.exe')
                if os.path.exists(encoder_path):
                    self.exe_path = encoder_path
                    break

        if os.path.exists(self.exe_path):
            log_info(f'Found w3strings encoder: {self.exe_path}')
        else:
            raise Exception('w3strings encoder couldn\'t be found')


    def execute(self, cmd: str):
        cmd = f'{self.exe_path} {cmd}'

        log_warning('Executing command:')
        log_warning(cmd)

        # we ignore stderr, because it contains only the thread panic message without any information that is helpful to us
        output = subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if logging_level > 0:
            print('=' * 100)
            lines = output.stdout.split('\n')
            for line in lines:
                self.log_encoder_output(line)
            print('=' * 100)
  
        if output.returncode != 0:
            raise Exception('Process exited with an error')

    # Returns the path to decoded file
    def decode(self, w3strings_path: str) -> str:
        log_info(f'Decoding {w3strings_path}...')
        self.execute(f'-d "{w3strings_path}"')
        return w3strings_path + '.csv' 

    # Returns the path to encoded file
    def encode(self, csv_path: str, id_space: int | None) -> str:
        cmd = f'-e "{csv_path}" '
        if id_space is None:
            DISABLE_ID_CHECK_FLAG = '--force-ignore-id-space-check-i-know-what-i-am-doing'
            log_warning(f'Disabling ID check in the encoder because of the existence of entries outside of a single mod ID range')
            cmd += DISABLE_ID_CHECK_FLAG
        else:
            cmd += f'-i {id_space}'

        log_info(f'Encoding {csv_path}...')
        self.execute(cmd)

        w3strings_path = csv_path + '.w3strings'
        ws_path = w3strings_path + '.ws'

        if os.path.exists(ws_path):
            log_info(f'Removing {ws_path}')
            os.remove(ws_path)

        return w3strings_path
    

    def log_encoder_output(self, line: str):
        if line.startswith('INFO'):
            log_info(line[7:])
        elif line.startswith('WARN'):
            log_warning(line[7:])
        elif line.startswith('ERROR'):
            log_error(line[8:])
        elif len(line) > 0:
            log_info(line)



###############################################################################################################################
# CSV FILE PARSING
###############################################################################################################################

class CsvAbbreviatedEntry:
    key_str: str
    text: str

    def __init__(self, key_str: str, text: str = "MISSING_LOCALISATION"):
        self.key_str = key_str
        self.text = text

    def __str__(self) -> str:
        return f'{self.key_str}|{self.text}'

    def into_complete(self, id: int, key_hex: str) -> CsvCompleteEntry:
        return CsvCompleteEntry(
            id,
            key_hex,
            self.key_str,
            self.text
        )


IdSpace = int | Literal["vanilla"]

class CsvCompleteEntry:
    id: int
    key_hex: str
    key_str: str
    text: str

    def __init__(self, id: int, key_hex: str, key_str: str, text: str) -> None:
        self.id = id
        self.key_hex = key_hex
        self.key_str = key_str
        self.text = text

    def __str__(self) -> str:
        return '|'.join([
            str(self.id).rjust(10, ' '),
            self.key_hex.rjust(8, ' '),
            self.key_str,
            self.text
        ])
    
        
    def id_space(self) -> IdSpace:
        if self.id not in MOD_ID_RANGE:
            return "vanilla"
        else:
            return (self.id % 2110000000) // 1000


class CsvCommentAttribute:
    key: str
    value: str

    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value

    def __str__(self) -> str:
        return f";{self.key}={self.value}"


def parse_entry(s: str) -> CsvAbbreviatedEntry | CsvCompleteEntry | CsvCommentAttribute | str:
    s = s.strip()
    if len(s) == 0:
        return str(s)
    elif s.startswith(';'):
        attrib = s[1:].split('=')
        # attribute should adhere to strict format
        # ;key=value
        # where key does not contain any spaces (like an identifier) and the entire lines has exactly one '=' character
        # because otherwise it's treated as regular informational comment
        if len(attrib) == 2 and attrib[0].count(' ') == 0:
            return CsvCommentAttribute(attrib[0], attrib[1])
        else:
            return str(s)

    split = s.strip().split('|')
    if len(split) == 2:
        return CsvAbbreviatedEntry(
            split[0], 
            split[1]
        )
    elif len(split) == 4:
        id: int
        try:
            id = int(split[0])
        except ValueError:
            raise Exception('Failed to parse id column to a number')

        return CsvCompleteEntry(
            id,
            split[1],
            split[2],
            split[3]
        )
    else:
        raise Exception(f'Invalid column count. Expected 2 or 4, got {len(split)}')


'''Input form of the document that can have features such as skipped header or abbreviated entries that will be converted into output document'''
class CsvInputDocument:
    target_lang: str | None
    header_lang_meta: str | None
    header_mod_id_space: int | None  # id space from a custom attribute in the header
    entries_abbrev: list[CsvAbbreviatedEntry]
    entries_complete: list[CsvCompleteEntry]
    content_mod_id_space: int | None  # id space deduced from id column in entries; None if there are only vanilla Ids and/or abbreviated entries
    has_vanilla_entries: bool

    def __init__(self, file_path: str):
        encoding = guess_file_encoding(file_path)
        log_info(f'Reading {file_path}. Detected encoding: {encoding}')
        with io.open(file_path, mode='r', encoding=encoding) as file:
            self.read_target_lang(file_path)

            file_lines = file.readlines()

            try:
                self.read_header(file_lines)
            except Exception as e:
                raise Exception(f'Failed to read file header:\n{e}')

            try:
                self.read_content(file_lines)
            except Exception as e:
                raise Exception(f'Failed to read file content:\n{e}')
  

    def read_target_lang(self, file_path: str):
        self.target_lang = None

        basename = os.path.basename(file_path)
        basename_parts = basename.split('.')[:-1] # without the extension

        for part in basename_parts:
            if part in ALL_LANGS:
                self.target_lang = part
                log_info(f'Detected target language in file name: {self.target_lang}')
                break


    def read_header(self, file_lines: list[str]):
        self.header_lang_meta = None
        if self.target_lang is not None:
            self.header_lang_meta = ALL_LANGS_META[self.target_lang]
            log_info(f'Detected language meta "{self.header_lang_meta}" based on target language')

        self.header_mod_id_space = None
        for line in file_lines:
            if not line.startswith(';'):
                break
            comment = line.strip().replace(' ', '')
            attrib = parse_entry(comment)
            if isinstance(attrib, CsvCommentAttribute):
                match attrib.key:
                    case "meta[language":
                        lang_meta = attrib.value[:-1]
                        if lang_meta in ALL_LANGS_META.values():
                            self.header_lang_meta = lang_meta
                        else:
                            raise Exception(f'Invalid header language meta: {lang_meta}. Available values: {ALL_LANGS_META.values()}')
                
                        log_info(f'Detected language meta "{self.header_lang_meta}" based on file header')
                    case "idspace":
                        try:
                            self.header_mod_id_space = int(attrib.value)
                        except ValueError:
                            raise Exception('Failed to parse id space value into a number')
                        
                        if self.header_mod_id_space not in range(0, 10000):
                            raise Exception('Id space value falls out of 0-9999 range')
                        
                        log_warning(f'Detected mod id space in the header: {self.header_mod_id_space}')
                    case _:
                        pass

        if self.target_lang is None and self.header_lang_meta not in (None, 'cleartext'):
            # if it's not cleartext, it's the same as the proper file name
            log_info(f'Detected target language based on language meta: {self.target_lang}')
            self.target_lang = self.header_lang_meta



    def read_content(self, file_lines: list[str]):
        self.entries_abbrev = []
        self.entries_complete = []

        for i, line in enumerate(file_lines):
            if not line.startswith(';'):
                try:
                    entry = parse_entry(line)
                    if isinstance(entry, CsvAbbreviatedEntry):
                        self.entries_abbrev.append(entry)
                    elif isinstance(entry, CsvCompleteEntry):
                        self.entries_complete.append(entry)
                except Exception as e:
                    raise Exception(f'Failed to read line {i}:\n{e}')

        if len(self.entries_abbrev) + len(self.entries_complete) == 0:
            raise Exception('File has no data to encode')
        
        all_ids = [entry.id for entry in self.entries_complete]
        duplicate_ids = [id for id in all_ids if all_ids.count(id) > 1]
        if len(duplicate_ids) > 1:
            raise Exception(f'There are multiple entries with the same id: {duplicate_ids}')
        
        self.read_content_id_space()
        

    def read_content_id_space(self):
        id_spaces = set[IdSpace]([entry.id_space() for entry in self.entries_complete])
        self.has_vanilla_entries = "vanilla" in id_spaces

        if self.has_vanilla_entries:
            log_warning('Detected vanilla strings')

        mod_id_spaces = set([id_space for id_space in id_spaces if isinstance(id_space, int)])
        if len(mod_id_spaces) == 0:
            self.content_mod_id_space = None
        elif len(mod_id_spaces) == 1:
            self.content_mod_id_space = mod_id_spaces.pop()
            log_warning(f'Detected mod id space in entries: {self.content_mod_id_space}')
        else:
            raise Exception(f'There are entries for multiple mod id spaces: {mod_id_spaces}')
        
        if self.header_mod_id_space is not None and self.content_mod_id_space is not None:
            if self.header_mod_id_space != self.content_mod_id_space:
                raise Exception(f'Id space in the header ({self.header_mod_id_space}) and id space used in the entries ({self.content_mod_id_space}) do not match')
        elif self.header_mod_id_space is None and self.content_mod_id_space is None and len(self.entries_abbrev) > 0:
            raise Exception('No id space was provided to complete abbreviated entries')


'''Processed form of the document that will be forwarded to w3strings for encoding'''
class CsvOutputDocument:
    target_lang: str
    header_lang_meta: str
    entries: list[CsvCompleteEntry]
    id_space: int | None # None means there are non-mod ids in the file and id check has to be force-disabled

    def __init__(self, target_lang: str, header_lang_meta: str, id_space: int | None, entries: list[CsvCompleteEntry]):
        self.target_lang = target_lang
        self.header_lang_meta = header_lang_meta
        self.id_space = id_space
        self.entries = entries

    def __str__(self) -> str:
        file_lines: list[str] = []

        file_lines.append(f';meta[language={self.header_lang_meta}]')
        file_lines.append(';       id|key(hex)|key(str)|text')
        file_lines.extend([str(entry) for entry in self.entries])

        return '\n'.join(file_lines)

    def save_to_file(self, file_path: str):
        with io.open(file_path, mode='w', encoding='UTF-8') as file:
            output_str = str(self)
            file.write(output_str)


def prepare_output_csv(input: CsvInputDocument) -> CsvOutputDocument:
    # default to english language meta if it wasn't deduced during parsing
    header_lang_meta: str
    if input.header_lang_meta is not None:
        header_lang_meta = input.header_lang_meta
    else:
        header_lang_meta = 'en'
        log_info('No language meta could be deduced. Defaulting to "en"')

    target_lang = input.target_lang or 'en'
    id_space = input.header_mod_id_space or input.content_mod_id_space

    output_entries = list[CsvCompleteEntry]()

    if id_space is not None and len(input.entries_abbrev) > 0:
        id_set = set([entry.id for entry in input.entries_complete])
        id_counter = MOD_ID_RANGE.start + id_space * 1000
        for entry in input.entries_abbrev:
            while id_counter in id_set:
                id_set.remove(id_counter)
                id_counter += 1
            complete = entry.into_complete(id_counter, '')
            output_entries.append(complete)
            # A chance for ID overflow is rather low, so we will ignore it
            id_counter += 1
            
    for entry in input.entries_complete:
        output_entries.append(entry)

    output_entries.sort(key=lambda entry: entry.id)

    return CsvOutputDocument(
        target_lang,
        header_lang_meta,
        id_space if not input.has_vanilla_entries else None,
        output_entries,
    )


def save_abbreviated_entries(entries: dict[str, list[CsvAbbreviatedEntry]], file_path: str):
    file_lines: list[str] = []
    file_lines.append(";idspace=????")

    for section, section_entries in entries.items():
        file_lines.append(f";section={section}")
        file_lines.extend([str(entry) for entry in section_entries])

    with io.open(file_path, mode="w", encoding="UTF-8") as f:
        f.write('\n'.join(file_lines))



'''Class made to as non-invasively as possible insert new entries into an existing CSV document'''
'''Doesn't validate and examine the file as thoroughly as CsvInputDocument does'''
class CsvMergingDocument:
    def __init__(self, file_path: str):
        self.file_path: str = file_path
        self.file_encoding: str = guess_file_encoding(file_path)

        self.file_lines: list[str | CsvCommentAttribute | CsvAbbreviatedEntry | CsvCompleteEntry] = [] # if str it's a regular comment or empty line
        self.sections: list[tuple[str, int]]  = [] # (section_name, line_idx)
        self.str_keys: set[str] = set()

        with io.open(file_path, mode="r", encoding=self.file_encoding) as f:
            for i, line in enumerate(f):
                try:
                    entry = parse_entry(line)
                    self.file_lines.append(entry)

                    if isinstance(entry, CsvAbbreviatedEntry) or isinstance(entry, CsvCompleteEntry):
                        self.str_keys.add(entry.key_str)
                except Exception as e:
                    raise Exception(f'Failed to read line {i}:\n{e}')

        for i, line in enumerate(self.file_lines):
            if isinstance(line, CsvCommentAttribute) and line.key == "section":
                self.sections.append((line.value, i))


    def save(self):
        log_info(f"Merging entries into an existing file...")
        with io.open(self.file_path, mode="w", encoding=self.file_encoding) as f:
            str_lines = [str(line) for line in self.file_lines]
            f.write('\n'.join(str_lines))


    def insert_entries(self, entries: list[CsvAbbreviatedEntry], target_section: str):
        # filter out entries that already exist in the document
        entries = list(filter(lambda e: e.key_str not in self.str_keys, entries))

        idx = self.section_range(target_section).stop
        self.file_lines[idx:idx] = entries

    def section_range(self, target_section: str) -> range:
        start_idx: int | None = None
        stop_idx: int | None = None

        # find the last line of target section
        for i, (section_name, section_line_idx) in enumerate(self.sections):
            if section_name == target_section:
                start_idx = section_line_idx + 1
                # if it's the last section, make stop the end of file
                if i == len(self.sections) - 1:
                    stop_idx = len(self.file_lines)
                # otherwise insert before the next section marker
                else:
                    stop_idx = self.sections[i + 1][1]
                break

        if start_idx is not None and stop_idx is not None:
            return range(start_idx, stop_idx)
        
        # add the section if there isn't one already
        self.file_lines.append(CsvCommentAttribute("section", target_section))
        section_line_idx = len(self.file_lines) - 1
        self.sections.append((target_section, section_line_idx))

        start_idx = section_line_idx + 1
        stop_idx = len(self.file_lines)

        return range(start_idx, stop_idx)
        



def merge_abbreviated_entries(entries: dict[str, list[CsvAbbreviatedEntry]], file_path: str):
    doc = CsvMergingDocument(file_path)
    for section, section_entries in entries.items():
        if len(section_entries) > 0:
            doc.insert_entries(section_entries, section)

    doc.save()


def save_or_merge_abbreviated_entries(entries: dict[str, list[CsvAbbreviatedEntry]], file_path: str):
    if os.path.exists(file_path):
        merge_abbreviated_entries(entries, file_path)
    else:
        save_abbreviated_entries(entries, file_path)



###############################################################################################################################
# XML FILE PARSING
###############################################################################################################################

# A new class, because native ElementTree.Element doesn't have support for easy node parent access
class ConfigXmlElement:
    element: ElementTree.Element

    parent: Any = None # can't use the same class type for it
    children: list[ConfigXmlElement]

    display_name: str
    custom_display_name: bool
    custom_names: bool
    non_localized: bool
    non_localized_except_first: bool


    # instantiate using base class object
    def __init__(self, element: ElementTree.Element, parent: Any = None):
        self.element = element
        self.parent = parent
        self.children = []
        self.display_name = ''
        self.custom_display_name = False
        self.custom_names = False
        self.non_localized = False
        self.non_localized_except_first = False

        try:
            self.display_name = element.attrib["displayName"]
            tags = element.attrib["tags"].split(";")
            if "customDisplayName" in tags:
                self.custom_display_name = True
            if "customNames" in tags:
                self.custom_names = True
            if "nonLocalized" in tags:
                self.non_localized = True
            if "nonLocalizedExceptFirst" in tags:
                self.non_localized_except_first = True
        except KeyError:
            pass

        for child in element:
            self.children.append(ConfigXmlElement(child, self))


    def loc_str_keys(self) -> list[str]:
        if self.display_name == "" or self.non_localized:
            return []
        
        match self.element.tag:
            case "Group":
                keys: list[str] = []

                panel_components = self.display_name.split('.')
                if not self.custom_display_name:
                    keys.extend([f'panel_{dn}' for dn in panel_components])
                else:
                    keys.extend(panel_components)
                
                if "PresetsArray" in [child.element.tag for child in self.children]:
                    keys.append(f'preset_{self.display_name.replace(".", "_")}')

                return keys
            case "Preset":
                return [f'preset_value_{self.display_name}']
            case "Var":
                if not self.custom_display_name:
                    return [f'option_{self.display_name}']
                else:
                    return [self.display_name]
            case "Option":
                var_node = cast(ConfigXmlElement, self.parent.parent)
                if var_node.non_localized or (var_node.non_localized_except_first and self.element.attrib["id"] != "0"):
                    return []
                elif not var_node.custom_names:
                    return [f'preset_value_{self.display_name}']
                else:
                    return [self.display_name]
            case _:
                return []

    def child_loc_str_keys(self) -> list[str]:
        if len(self.children) == 0:
            return []
        
        keys: list[str] = []
        for child in self.children:
            keys.extend(child.loc_str_keys())
            keys.extend(child.child_loc_str_keys())    

        return keys
    
    def all_loc_str_keys(self) -> list[str]:
        keys: list[str] = []
        keys.extend(self.loc_str_keys())
        keys.extend(self.child_loc_str_keys())
        return keys


def parse_config_xml_for_str_keys(xml_path: str, search: str) -> list[str]:
    encoding = guess_file_encoding(xml_path)
    log_info(f"Reading config XML {xml_path}. Detected encoding: {encoding}")

    keys: list[str] = []
    with io.open(xml_path, "r", encoding=encoding) as f:
        xml_str = f.read()
        root = ElementTree.fromstring(xml_str)
        config_xml = ConfigXmlElement(root)

        keys = remove_duplicate_keys_and_filter(config_xml.all_loc_str_keys(), search)

    log_info(f"Found {len(keys)} string keys in {xml_path}")
    return keys


def parse_bundled_xml_for_str_keys(xml_path: str, search: str) -> list[str]:
    encoding = guess_file_encoding(xml_path)
    log_info(f"Reading bundled XML {xml_path}. Detected encoding: {encoding}")

    keys: list[str] = []
    with io.open(xml_path, "r", encoding=encoding) as f:
        for _, elem in ElementTree.iterparse(f, events=["start"]):
            elem = cast(ElementTree.Element, elem)
            if elem.tag in BUNDLED_XML_LOCALIZATION_ATTRIBS:
                for attrib in BUNDLED_XML_LOCALIZATION_ATTRIBS[elem.tag]:
                    keys.append(elem.attrib.get(attrib, ''))

        keys = remove_duplicate_keys_and_filter(keys, search)

    log_info(f"Found {len(keys)} string keys in {xml_path}")
    return keys


def is_config_xml(xml_path: str) -> bool:
    encoding = guess_file_encoding(xml_path)
    with io.open(xml_path, "r", encoding=encoding) as f:
        _, root = next(ElementTree.iterparse(f, events=["start"]))
        root = cast(ElementTree.Element, root)
        if root.tag == "UserConfig":
            return True
        
    return False


def parse_xml_for_str_keys(xml_path: str, search: str) -> tuple[list[str], bool]:
    if is_config_xml(xml_path):
        return (parse_config_xml_for_str_keys(xml_path, search), True)
    else:
        return (parse_bundled_xml_for_str_keys(xml_path, search), False)



###############################################################################################################################
# WITCHERSCRIPT FILE PARSING
###############################################################################################################################

def parse_ws_for_str_keys(ws_path: str, search: str) -> list[str]:
    encoding = guess_file_encoding(ws_path)
    log_info(f"Reading WitcherScript {ws_path}. Detected encoding: {encoding}")

    possible_keys = list[str]()
    with io.open(ws_path, mode='r', encoding=encoding) as f:
        for line in f:
            quoted = line.split('"')[1::2]
            possible_keys.extend(quoted)

    possible_keys = remove_duplicate_keys_and_filter(possible_keys, search)

    log_info(f"Found {len(possible_keys)} string keys in {ws_path}")
    return possible_keys



###############################################################################################################################
# CLI
###############################################################################################################################

class CLIArguments:
    input_path: str
    output_path: str
    lang: str  # one of ALL_LANGS or 'all'
    keep_csv: bool
    search: str


def make_cli() -> CLIArguments:
    parser = argparse.ArgumentParser(
        description=f'w3stringsx v{W3STRINGSX_VERSION}\n'
                    'Script meant to provide an alternative CLI frontend for w3strings encoder '
                    'to make it simpler and faster to create localized Witcher 3 content',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='remarks:\n'
                '  * in the case of CSV file context, the output path must be a directory\n'
                '  * --language and --keep-csv arguments apply only to CSV file context\n'
                '  * --search option applies only to XML and WitcherScript contexts'
    )

    parser.add_argument(
        'input_path',
        help='path to a file [.w3strings, .csv, .xml, .ws] or a directory with [.xml, .ws] files',
        action='store'
    )

    parser.add_argument(
        '-o', '--output_path',
        help='path to the output; default: [input file\'s directory]',
        default='',
        action='store')
    
    parser.add_argument(
        '-l', '--language', 
        help=f'set the target encoding language, "all" will generate all possible variants; available: {ALL_LANGS + ["all"]}',
        default='all',
        dest='lang', action='store')

    parser.add_argument(
        '-k', '--keep-csv',
        help='keep the final form of the generated CSV file',
        dest='keep_csv', action='store_true')
    
    parser.add_argument(
        '-s', '--search',
        help='text that will be used to search localisation string keys; can accept regular expressions',
        default='',
        dest='search', action='store')
    
    parser.add_argument(
        '-w', '--warn',
        help='logging level that should be used; available: [0 - no logs, 1 - only errors, 2 - errors and warnings, 3 - everything]; default: 3',
        default=3,
        dest='warn_level', action='store')
    
    args = parser.parse_args()

    cli = CLIArguments()
    cli.input_path = str(args.input_path)
    cli.output_path = str(args.output_path)
    cli.lang = str(args.lang)
    cli.keep_csv = bool(args.keep_csv)
    cli.search = str(args.search)

    global logging_level
    try:
        logging_level = int(args.warn_level)
    except ValueError:
        raise Exception('Invalid logging level value')

    return cli


def preprocess_cli_args(args: CLIArguments):
    if not os.path.exists(args.input_path):
        raise Exception(f'Path does not exist: "{args.input_path}"')
    
    args.input_path = os.path.realpath(args.input_path)

    if args.lang not in ALL_LANGS and args.lang != 'all':
        raise Exception(f'Invalid value for the --language option: {args.lang}')
    
    if args.output_path != '':
        if not os.path.exists(args.output_path):
            if not maybeisfile(args.output_path):
                log_warning('Specified output directory does not exist. Attempting to create one...')
                try:
                    os.mkdir(args.output_path)
                except FileNotFoundError:
                    raise Exception('Unable to create output directory. The parent of this directory does not exist.')
                log_warning(f'Directory {args.output_path} created successfully')
    else:
        args.output_path = os.path.dirname(args.input_path)
        log_info(f'Ouput path set to directory {args.output_path}')

    args.output_path = os.path.realpath(args.output_path)

    try:
        re.search(args.search, "test")
    except Exception as e:
        raise Exception(f'Invalid regex search string: {e}')


###############################################################################################################################
# MAIN
###############################################################################################################################

def main():
    args = make_cli()
    preprocess_cli_args(args)

    input_type = InputPathType.from_path(args.input_path)

    if input_type in (InputPathType.W3STRINGS_FILE, InputPathType.CSV_FILE):
        encoder = W3StringsEncoder()
        scratch = ScratchFolder(args.input_path)

        match input_type:
            case InputPathType.W3STRINGS_FILE:
                w3strings_context_work(encoder, scratch, args)
            case InputPathType.CSV_FILE:
                csv_context_work(encoder, scratch, args)
    else:
        match input_type:
            case InputPathType.XML_FILE:
                xml_context_work(args)
            case InputPathType.WITCHERSCRIPT_FILE:
                witcherscript_context_work(args)
            case InputPathType.DIRECTORY:
                directory_context_work(args)
            case _:
                raise Exception(f'Unsupported file type: {os.path.basename(args.input_path)}')



def w3strings_context_work(encoder: W3StringsEncoder, scratch: ScratchFolder, args: CLIArguments):
    csv_file = encoder.decode(scratch.input_copy_path)
    lf_to_crlf(csv_file) # for whatever reason encoder saves the file with unix line endings

    output_path = resolve_output_path(scratch.input_copy_path, args.output_path, "{stem}.csv")
    shutil.copy(csv_file, output_path)

    log_info(f'{args.input_path} has been successfully decoded into {output_path}')


def csv_context_work(encoder: W3StringsEncoder, scratch: ScratchFolder, args: CLIArguments):
    if os.path.isfile(args.output_path) or maybeisfile(args.output_path):
        raise Exception('CSV context requires the output path to point to a directory')

    input_doc = CsvInputDocument(scratch.input_copy_path)
    output_doc = prepare_output_csv(input_doc)
    output_doc_path = resolve_output_path(scratch.input_copy_path, scratch.folder_path, "{stem}.w3stringsx.csv")
    output_doc.save_to_file(output_doc_path)

    try:
        w3strings_file = encoder.encode(output_doc_path, output_doc.id_space)
        langs = ALL_LANGS if args.lang == 'all' else [args.lang]
        for lang in langs:
            copied = os.path.join(args.output_path, f'{lang}.w3strings')
            log_info(f'Creating {copied}')
            shutil.copy(w3strings_file, copied)
  
    finally:
        if args.keep_csv:
            log_info(f'Saving prepared {os.path.basename(output_doc_path)} to {args.output_path}')
            shutil.copy(output_doc_path, args.output_path)

    log_info(f'{args.input_path} has been successfully encoded into w3strings file(s) in {args.output_path}')


def xml_context_work(args: CLIArguments):
    keys, is_config = parse_xml_for_str_keys(args.input_path, args.search)
    entries = [CsvAbbreviatedEntry(key) for key in keys]
    section_name = COMMENT_SECTION_MENU if is_config else COMMENT_SECTION_BUNDLE
    section = {section_name : entries}

    csv_path = resolve_output_path(args.input_path, args.output_path, "{stem}.en.csv")
    save_or_merge_abbreviated_entries(section, csv_path)

    log_info(f'Localisation keys from {args.input_path} have been successfully saved to {csv_path}')


def witcherscript_context_work(args: CLIArguments):
    if args.search == "":
        raise Exception("No search string specified. Use the --search option")
    
    keys = sorted(parse_ws_for_str_keys(args.input_path, args.search))
    entries = [CsvAbbreviatedEntry(key) for key in keys]
    section = {COMMENT_SECTION_SCRIPTS : entries}

    csv_path = resolve_output_path(args.input_path, args.output_path, "{stem}.en.csv")
    save_or_merge_abbreviated_entries(section, csv_path)

    log_info(f'Localisation keys from {args.input_path} have been successfully saved to {csv_path}')


def directory_context_work(args: CLIArguments):
    if args.search == "":
        raise Exception("No search string specified. Use the --search option")

    menu_keys = list[str]()
    bundle_keys = list[str]()
    script_keys = list[str]()
    for root, _, files in os.walk(args.input_path):
        for file in files:
            path = os.path.join(root, file)
            match InputPathType.from_path(path):
                case InputPathType.WITCHERSCRIPT_FILE:
                    script_keys.extend(parse_ws_for_str_keys(path, args.search))
                case InputPathType.XML_FILE:
                    keys, for_menu = parse_xml_for_str_keys(path, args.search)
                    if for_menu:
                        menu_keys.extend(keys)
                    else:
                        bundle_keys.extend(keys)
                case _:
                    pass

    menu_keys = remove_duplicate_keys_and_filter(menu_keys, '')

    bundle_keys = sorted(remove_duplicate_keys_and_filter(bundle_keys, ''))
    # remove keys that appear across multiple source types
    bundle_keys = key_list_difference(bundle_keys, menu_keys)

    script_keys = sorted(remove_duplicate_keys_and_filter(script_keys, ''))
    script_keys = key_list_difference(script_keys, menu_keys)
    script_keys = key_list_difference(script_keys, bundle_keys)

    sections = {
        COMMENT_SECTION_MENU: [CsvAbbreviatedEntry(key) for key in menu_keys],
        COMMENT_SECTION_BUNDLE: [CsvAbbreviatedEntry(key) for key in bundle_keys],
        COMMENT_SECTION_SCRIPTS: [CsvAbbreviatedEntry(key) for key in script_keys]
    }

    csv_path = resolve_output_path(args.input_path, args.output_path, "{stem}.en.csv")
    save_or_merge_abbreviated_entries(sections, csv_path)

    log_info(f'Localisation keys from {args.input_path} have been successfully saved to {csv_path}')




if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log_error(f'{e}')
        sys.exit(-1)
