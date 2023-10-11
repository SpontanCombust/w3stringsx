'''Helper script that automates the process of working with w3strings encoder'''

import getopt
import io
import os
import sys
from typing import Literal


ALL_LANGS: list[str] = ['an', 'br', 'cn', 'cz', 'de', 'en', 'es', 'esmx', 'fr', 'hu', 'it', 'jp', 'kr', 'pl', 'ru', 'tr', 'zh']
ALL_LANGS_META: dict[str, str] = {
    'ar':   'cleartext',
    'br':   'cleartext',
    'cn':   'cleartext',
    'cz':   'cz',
    'de':   'de',
    'en':   'en',
    'es':   'es',
    'esMX': 'cleartext',
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

# TODO turn into class
ENCODER = os.path.join(os.path.split(__file__)[0], 'w3strings.exe')
if not os.path.exists(ENCODER):
    print('[Error] Encoder not found! Make sure to place the script in the same directory as the encoder')
    sys.exit(-1)



IdSpace = int | Literal["vanilla"]

'''Content line from the input CSV document, it can have id and key_hex columns omitted'''
class CsvInputEntry:
    id: int | None
    key_hex: str | None
    key_str: str
    text: str

    def __init__(self, s: str):
        split = s.split('|')
        size = len(split)
        if size == 2:
            self.id = None
            self.key_hex = None
            self.key_str = split[0]
            self.text = split[1]
        elif size == 4:
            id: int
            try:
                id = int(split[0])
            except ValueError:
                raise Exception('Failed to parse id column to a number')

            self.id = id
            self.key_hex = split[1]
            self.key_str = split[2]
            self.text = split[3]
        else:
            raise Exception(f'Invalid column count. Expected 2 or 4, got {len(split)}')

    def is_abbreviated(self) -> bool:
        return self.id is None

    def id_space(self) -> IdSpace | None:
        if self.id is None:
            return None
        elif self.id not in MOD_ID_RANGE:
            return "vanilla"
        else:
            return (self.id % 2110000000) // 1000


'''Input form of the document that can have features such as skipped header or abbreviated entries that will be converted into output document'''
class CsvInputDocument:
    target_lang: str | None
    header_lang_meta: str | None
    header_id_space: int | None  # id space from a custom attribute in the header
    entries: list[CsvInputEntry]
    content_id_space: int | None  # id space deduced from id column in entries; None if there are only vanilla Ids and/or abbreviated entries
    has_vanilla_entries: bool

    def __init__(self, file_path: str):
        with io.open(file_path, mode='r', encoding='UTF-8') as file:
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

        basename = os.path.basename(file_path)[1]
        basename_parts = basename.split('.')[:-1] # without the extension

        for part in basename_parts:
            if part in ALL_LANGS:
                self.target_lang = part
                break


    def read_header(self, file_lines: list[str]):
        self.header_lang_meta = None if self.target_lang is None else ALL_LANGS_META[self.target_lang]
        self.header_id_space = None
        for line in file_lines:
            if not line.startswith(';'):
                break
            comment = line.strip().replace(' ', '')
            if comment.startswith(';meta[language='):
                lang_meta = comment[15:-1]
                if lang_meta in ALL_LANGS_META.values():
                    self.header_lang_meta = lang_meta
                else:
                    raise Exception(f'Invalid header language meta: {lang_meta}')
            elif comment.startswith(';idspace='):
                try:
                    self.header_id_space = int(comment[9:])
                except ValueError:
                    raise Exception('Failed to parse id space value into a number')
                
                if self.header_id_space not in range(0, 10000):
                    raise Exception('Id space value falls out of 0-9999 range')


    def read_content(self, file_lines: list[str]):
        for i, line in enumerate(file_lines):
            if not line.startswith(';'):
                try:
                    input_entry = CsvInputEntry(line)
                    self.entries.append(input_entry)
                except Exception as e:
                    raise Exception(f'Failed to read line {i}:\n{e}')

        if len(self.entries) == 0:
            raise Exception('File has no data to encode')
        
        all_ids = [entry.id for entry in self.entries if entry.id is not None]
        duplicate_ids = [id for id in all_ids if all_ids.count(id) > 1]
        if len(duplicate_ids) > 1:
            raise Exception(f'There are multiple entries with the same id: {duplicate_ids}')

        if self.header_id_space is None and any(entry.is_abbreviated() for entry in self.entries):
            raise Exception('No id space was provided in the header to complete abbreviated entries')
        
        self.read_content_id_space()
        

    def read_content_id_space(self):
        id_spaces = set[IdSpace | None](map(lambda entry: entry.id_space(), self.entries))
        self.has_vanilla_entries = "vanilla" in id_spaces

        mod_id_spaces = set[int]()
        for id_space in id_spaces:
            if isinstance(id_space, int):
                mod_id_spaces.add(id_space)

        if len(mod_id_spaces) == 0:
            self.content_id_space = None
        elif len(mod_id_spaces) == 1:
            self.content_id_space = mod_id_spaces.pop()

            if self.header_id_space is not None:
                if self.header_id_space != self.content_id_space:
                    raise Exception(f'Id space in the header ({self.header_id_space}) and id space used in the entries ({self.content_id_space}) are not the same')
                else:
                    print('[Warning] Using complete and abbreviated entries in one file may cause undefined behaviour. Please settle for one or the other')
        else:
            raise Exception(f'There are entries for multiple mod id spaces: {mod_id_spaces}')


'''CSV content line in a form prepared for encoding'''
class CsvOutputEntry:
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
            self.key_hex.rjust(8, '0'),
            self.key_str,
            self.text
        ])


'''Processed form of the document that will be forwarded to w3strings for encoding'''
class CsvOutputDocument:
    header_lang_meta: str
    entries: list[CsvOutputEntry]
    id_space: int | None # None means there are non-mod ids in the file and id check has to be force-disabled

    def __init__(self, header_lang_meta: str, entries: list[CsvOutputEntry], id_space: int | None):
        self.header_lang_meta = header_lang_meta
        self.entries = entries
        self.id_space = id_space

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



def prepare_output_entry(input_entry: CsvInputEntry, fallback_id: int | None) -> tuple[CsvOutputEntry, bool]:
    id: int
    used_fallback: bool
    if input_entry.id is not None:
        id = input_entry.id
        used_fallback = False
    elif fallback_id is not None:
        id = fallback_id
        used_fallback = True
    else:
        raise Exception('No line id provided')
    
    entry = CsvOutputEntry(
        id,
        input_entry.key_hex or '00000000',
        input_entry.key_str,
        input_entry.text
    )

    return (entry, used_fallback)


def prepare_output_csv(input: CsvInputDocument) -> CsvOutputDocument:
    # default to english language meta if it wasn't deduced during parsing
    header_lang_meta = input.header_lang_meta or 'en'
    id_space = input.header_id_space or input.content_id_space

    output_entries = list[CsvOutputEntry]()
    if id_space is not None:
        id_counter = MOD_ID_RANGE.start + id_space
        for entry in input.entries:
            output_entry, entry_was_abbreviated = prepare_output_entry(entry, id_counter)
            output_entries.append(output_entry)
            if entry_was_abbreviated:
                id_counter += 1
    else:
        for entry in input.entries:
            output_entry, _ = prepare_output_entry(entry, None)
            output_entries.append(output_entry)

    return CsvOutputDocument(
        header_lang_meta,
        output_entries,
        id_space
    )



def decode(w3strings_path: str):
    cmd = f'{ENCODER} -d {w3strings_path}'
    print(cmd)
    os.system(cmd)


def encode(csv_path: str, lang: str | None, keep_csv: bool):
    if lang is not None and lang not in ALL_LANGS and lang != 'all':
        raise Exception(f'Language {lang} is invalid')

    input_doc = CsvInputDocument(csv_path)
    output_doc = prepare_output_csv(input_doc)
    output_doc.save_to_file('tmp.w3stringsx.csv') # FIXME temporary

    cmd = f'{ENCODER} -e {csv_path} '
    if output_doc.id_space is None:
        force_opt = '--force-ignore-id-space-check-i-know-what-i-am-doing'
        print(f'[Warning] Detected vanilla IDs in the file, using "{force_opt}" option to disable ID check in the encoder')
        cmd += force_opt
    else:
        cmd += f'-i {output_doc.id_space}'

    print(cmd)
    os.system(cmd)
    # TODO remove garbage


def print_help():
    print('Helper script that automates the process of working with w3strings encoder')
    print()
    print('USAGE:')
    print('\tpython w3stringsx.py [OPTIONS] <INPUT_FILE>')
    print()
    print('ARGS:')
    print('\t<INPUT_FILE>   - path to either .csv file (to encode) or .w3strings (to decode)')
    print()
    print('OPTIONS:')
    print('\t-h, --help     - print help')
    print('\t-l, --lang     - set the target encoding language, "all" will generate w3strings files for all languages; by default deduced from the CSV file')
    print('\t-k, --keep     - keep end result CSV')


def main(argv: list[str]):
    if len(argv) < 2:
        raise Exception('No input arguments provided')

    if argv[1] in ('-h', '--help'):
        print_help()
        return

    file_path = argv[1]
    lang = None
    keep_output_csv = False

    if not os.path.exists(file_path):
        raise Exception(f'Path does not exist: "{file_path}"')
    elif not os.path.isfile(file_path):
        raise Exception(f'Path does not describe a file: "{file_path}"')

    opts, _ = getopt.getopt(argv[2:], 'hl:k', ['help', 'lang=', 'keep'])
    for opt, arg in opts:
        if opt in ('-l', '--lang'):
            lang = arg.lstrip(' =')
        if opt in ('-k', '--keep'):
            keep_output_csv = True

    _, ext = os.path.splitext(file_path)
    if ext == '.w3strings':
        decode(file_path)
    elif ext == '.csv':
        encode(file_path, lang, keep_output_csv)
    else:
        raise Exception(f'Unsupported file type: "{ext}"')



if __name__ == '__main__':
    main(sys.argv)
