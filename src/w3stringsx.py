from __future__ import annotations
import argparse
import io
import os
import shutil
import subprocess
import sys
from typing import Literal


###############################################################################################################################
# CONSTANTS
###############################################################################################################################

W3STRINGSX_VERSION = '1.0.0'

ALL_LANGS: list[str] = ['an', 'br', 'cn', 'cz', 'de', 'en', 'es', 'esmx', 'fr', 'hu', 'it', 'jp', 'kr', 'pl', 'ru', 'tr', 'zh']
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



###############################################################################################################################
# UTILITIES
###############################################################################################################################

def log_info(s: str):
    print(f'[Info] {s}')

def log_warning(s: str):
    COLOR_WARN = '\033[93m'
    print(f'{COLOR_WARN}[Warning] {s}')

def log_error(s: str):
    COLOR_ERROR = '\033[91m'
    print(f'{COLOR_ERROR}[Error] {s}')



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
        print('Executing command:')
        print(cmd)

        try:
            print('=' * 60)
            subprocess.run(cmd, shell=True, check=True, capture_output=True)
        except Exception:
            raise Exception('Process exited with an error')
        finally:
            print('=' * 60)


    def decode(self, w3strings_path: str) -> str:
        log_info(f'Decoding {w3strings_path}...')
        self.execute(f'-d {w3strings_path}')
        return w3strings_path + '.csv' 

    def encode(self, csv_path: str, id_space: int | None) -> str:
        cmd = f'-e {csv_path} '
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



###############################################################################################################################
# CSV FILE PARSING
###############################################################################################################################

class CsvAbbreviatedEntry:
    key_str: str
    text: str

    def __init__(self, key_str: str, text: str):
        self.key_str = key_str
        self.text = text

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
            self.key_hex,
            self.key_str,
            self.text
        ])
    
        
    def id_space(self) -> IdSpace:
        if self.id not in MOD_ID_RANGE:
            return "vanilla"
        else:
            return (self.id % 2110000000) // 1000
        

def parse_entry(s: str) -> CsvAbbreviatedEntry | CsvCompleteEntry:
    split = s.split('|')
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
            if comment.startswith(';meta[language='):
                lang_meta = comment[15:-1]
                if lang_meta in ALL_LANGS_META.values():
                    self.header_lang_meta = lang_meta
                else:
                    raise Exception(f'Invalid header language meta: {lang_meta}. Available values: {ALL_LANGS_META.values()}')
     
                log_info(f'Detected language meta "{self.header_lang_meta}" based on file header')

            elif comment.startswith(';idspace='):
                try:
                    self.header_mod_id_space = int(comment[9:])
                except ValueError:
                    raise Exception('Failed to parse id space value into a number')
                
                if self.header_mod_id_space not in range(0, 10000):
                    raise Exception('Id space value falls out of 0-9999 range')
                
                log_info(f'Detected id space {self.header_mod_id_space} in the header. It will be used to complete abbreviated entries')

        if self.target_lang is None and self.header_lang_meta not in (None, 'cleartext'):
            # if it's not cleartext, it's the same as the proper file name
            log_info(f'Detected target language based on language meta: {self.target_lang}')
            self.target_lang = self.header_lang_meta



    def read_content(self, file_lines: list[str]):
        for i, line in enumerate(file_lines):
            if not line.startswith(';'):
                try:
                    entry = parse_entry(line)
                    if isinstance(entry, CsvAbbreviatedEntry):
                        self.entries_abbrev.append(entry)
                    else:
                        self.entries_complete.append(entry)
                except Exception as e:
                    raise Exception(f'Failed to read line {i}:\n{e}')

        if len(self.entries_abbrev) + len(self.entries_complete) == 0:
            raise Exception('File has no data to encode')
        
        all_ids = [entry.id for entry in self.entries_complete]
        duplicate_ids = [id for id in all_ids if all_ids.count(id) > 1]
        if len(duplicate_ids) > 1:
            raise Exception(f'There are multiple entries with the same id: {duplicate_ids}')

        if self.header_mod_id_space is None and len(self.entries_abbrev) > 0:
            raise Exception('No id space was provided in the header to complete abbreviated entries')
        
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
            log_info(f'Detected mod id space: {self.content_mod_id_space}')

            if self.header_mod_id_space is not None:
                if self.header_mod_id_space != self.content_mod_id_space:
                    raise Exception(f'Id space in the header ({self.header_mod_id_space}) and id space used in the entries ({self.content_mod_id_space}) are not the same')
                else:
                    log_warning('Using complete and abbreviated entries in one file may cause ID overlap. Please settle for one or the other')
        else:
            raise Exception(f'There are entries for multiple mod id spaces: {mod_id_spaces}')


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
        id_counter = MOD_ID_RANGE.start + id_space
        for entry in input.entries_abbrev:
            complete = entry.into_complete(id_counter, '')
            output_entries.append(complete)
            id_counter += 1
            
    for entry in input.entries_complete:
        output_entries.append(entry)

    return CsvOutputDocument(
        target_lang,
        header_lang_meta,
        id_space,
        output_entries,
    )




###############################################################################################################################
# CLI
###############################################################################################################################

class CLIArguments:
    input_file: str
    output_dir: str
    lang: str  # one of ALL_LANGS or 'all'
    keep_csv: bool

def make_cli() -> CLIArguments:
    parser = argparse.ArgumentParser(
        description=f'w3stringsx v{W3STRINGSX_VERSION}\n'
                    'Script meant to provide an alternative CLI frontend for w3strings encoder '
                    'to make it simpler and faster to create localized Witcher 3 content',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        'input_file',
        help='path to either .csv file (to encode) or .w3strings (to decode)',
        action='store'
    )

    parser.add_argument(
        '-o', '--output_dir',
        help='output directory for resulting files [default is input file\'s directory]',
        action='store')
    
    parser.add_argument(
        '-l', '--language', 
        help=f'set the target encoding language, "all" will generate all possible variants; available: {ALL_LANGS + ["all"]}',
        default='all',
        dest='lang', action='store')

    parser.add_argument(
        '-k', '--keep-csv',
        help='keep the final form of the CSV file generated during preperation for encoding',
        dest='keep_csv', action='store_true')
    
    args = parser.parse_args()

    cli = CLIArguments()
    cli.input_file = str(args.input_file)
    cli.output_dir = str(args.output_dir) if args.output_dir is not None else '' 
    cli.lang = str(args.lang)
    cli.keep_csv = bool(args.keep_csv) or False

    return cli


def preprocess_cli_args(args: CLIArguments):
    if not os.path.exists(args.input_file):
        raise Exception(f'File does not exist: "{args.input_file}"')
    elif not os.path.isfile(args.input_file):
        raise Exception(f'Path does not describe a file: "{args.input_file}"')
    
    args.input_file = os.path.realpath(args.input_file)

    if args.lang not in ALL_LANGS and args.lang != 'all':
        raise Exception(f'Invalid value for the --language option: {args.lang}')
    
    if args.output_dir != '':
        if not os.path.exists(args.output_dir):
            log_warning('Specified output directory does not exist. Attempting to create one...')
            try:
                os.mkdir(args.output_dir)
            except FileNotFoundError:
                raise Exception('Unable to create output directory. The parent of this directory does not exist.')
            log_warning(f'Directory {args.output_dir} created successfully')
    else:
        args.output_dir = os.path.dirname(args.input_file)
        log_info(f'Ouput directory set to {args.output_dir}')

    args.output_dir = os.path.realpath(args.output_dir)


###############################################################################################################################
# MAIN
###############################################################################################################################

def main():
    args = make_cli()
    encoder = W3StringsEncoder()

    preprocess_cli_args(args)
    
    _, ext = os.path.splitext(args.input_file)
    if ext not in ('.w3strings', '.csv'):
        raise Exception(f'Unsupported file type: "{ext}"')

    match ext:
        case '.w3strings':
            w3strings_context_work(encoder, args)
        case '.csv':
            csv_context_work(encoder, args)


def w3strings_context_work(encoder: W3StringsEncoder, args: CLIArguments):
    csv_file = encoder.decode(args.input_file)
    copied = os.path.join(args.output_dir, os.path.basename(csv_file))

    shutil.copy(csv_file, copied)
    os.remove(csv_file)

    log_info(f'{args.input_file} has been successfully decoded into {copied}')


def csv_context_work(encoder: W3StringsEncoder, args: CLIArguments):   
    input_doc = CsvInputDocument(args.input_file)
    output_doc = prepare_output_csv(input_doc)

    output_file_basename = args.input_file[:-4] + '.w3stringsx.csv'
    output_file = os.path.join(args.output_dir, output_file_basename)

    log_info(f'Creating temporary file {output_file}')
    output_doc.save_to_file(output_file)

    try:
        w3strings_file = encoder.encode(output_file, output_doc.id_space)
        if args.lang == 'all':
            for lang in ALL_LANGS:
                copied = os.path.join(args.output_dir, f'{lang}.w3strings')
                shutil.copy(w3strings_file, copied)
            os.remove(w3strings_file)
        else:
            copied = os.path.join(args.output_dir, f'{args.lang}.w3strings')
            shutil.copy(w3strings_file, copied)
            os.remove(w3strings_file)
            
        log_info(f'{args.input_file} has been successfully encoded into file(s) in {args.output_dir}')
    finally:
        if not args.keep_csv:
            os.remove(output_file)
            log_info(f'Removing temporary file {output_file}')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log_error(f'{e}')
        sys.exit(-1)
