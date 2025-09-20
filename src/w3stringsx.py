from __future__ import annotations
import argparse
from enum import Enum
import logging
import os
import re
import shutil
import sys

from w3stringsx import W3STRINGSX_VERSION
from w3stringsx.lib.localization import ALL_LANGS
from w3stringsx.lib.logging import *
from w3stringsx.lib.encoder import *
from w3stringsx.lib.w3strings_csv import *
from w3stringsx.lib.w3strings_csv_encoding_preprocessor import *
from w3stringsx.lib.sectioned_w3strings_csv import *
from w3stringsx.lib.xml_parsing import *
from w3stringsx.lib.ws_parsing import *
from w3stringsx.lib.directory_parsing import *
from w3stringsx.lib.utils import *


logger = get_logger()


###############################################################################################################################
# CONSTANTS AND ENUMS
###############################################################################################################################

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
                
PARSED_STR_KEYS_CSV_HEADER = W3StringsCsvAttributeComment('mod_id', '?????')


###############################################################################################################################
# CLI
###############################################################################################################################

class CLIArguments:
    input_path: str
    output_dir: str
    lang: str  # one of ALL_LANGS or 'all'
    keep_csv: bool
    search: str
    warn_level: int


def make_cli() -> CLIArguments:
    parser = argparse.ArgumentParser(
        description=f'w3stringsx v{W3STRINGSX_VERSION}\n'
                    'https://github.com/SpontanCombust/w3stringsx\n\n'
                    'Script acting as an alternative CLI frontend for w3strings encoder '
                    'while also providing additional functionalities to make working with localized Witcher 3 content easier and faster.',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='remarks:\n'
                '  * --language and --keep-csv arguments apply only to CSV file context\n'
                '  * --search option applies only to XML and WitcherScript contexts'
    )

    parser.add_argument(
        'input_path',
        help='path to a file [.w3strings, .csv, .xml, .ws] or a directory with [.xml, .ws] files',
        action='store'
    )

    parser.add_argument(
        '-o', '--output_dir',
        help='output directory to place the output in; default: [input file\'s directory]',
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
    cli.output_dir = str(args.output_dir)
    cli.lang = str(args.lang)
    cli.keep_csv = bool(args.keep_csv)
    cli.search = str(args.search)

    try:
        cli.warn_level = int(args.warn_level)
    except ValueError:
        raise Exception('Invalid logging level value')

    return cli


def preprocess_cli_args(args: CLIArguments):
    if not os.path.exists(args.input_path):
        raise Exception(f'Path does not exist: "{args.input_path}"')
    
    args.input_path = os.path.realpath(args.input_path)

    if args.lang not in ALL_LANGS and args.lang != 'all':
        raise Exception(f'Invalid value for the --language option: {args.lang}')
    
    if args.output_dir != '':
        if not os.path.isdir(args.output_dir):
            if os.path.isfile(args.output_dir):
                raise Exception("Specified output path points to an existing regular path instead of a directory.")
            if not os.path.isdir(os.path.dirname(args.output_dir)):
                raise Exception("Parent directory of the specified output path does not exist")

            logger.warning('Specified output directory does not exist. Attempting to create one...')
            try:
                os.mkdir(args.output_dir)
            except Exception as ex:
                raise Exception('Could not create output directory.', ex)
            logger.warning(f'Directory {args.output_dir} created successfully')
    else:
        # default to the parent directory of the input
        args.output_dir = os.path.dirname(args.input_path)
        logger.info(f'Ouput path set to directory {args.output_dir}')

    args.output_dir = os.path.realpath(args.output_dir)

    try:
        re.search(args.search, "test")
    except Exception as e:
        raise Exception(f'Invalid regex search string: {e}')


###############################################################################################################################
# MAIN
###############################################################################################################################

def main():
    # if -h flag is set it will forcefully exit the function
    args = make_cli()

    log_level = logging.INFO
    if args.warn_level == 0:
        # allowing only logs above CRITICAL level effectively should disable all logs
        log_level = logging.CRITICAL + 1 
    elif args.warn_level == 1:
        log_level = logging.ERROR
    elif args.warn_level == 2:
        log_level = logging.WARNING

    init_logger(log_level)

    try:
        preprocess_cli_args(args)

        input_type = InputPathType.from_path(args.input_path)

        if input_type in (InputPathType.W3STRINGS_FILE, InputPathType.CSV_FILE):
            encoder = W3StringsEncoder()
            scratch = ScratchFolder(os.path.dirname(args.input_path))

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
    except Exception as e:
        logger.error(f'{e}')
        sys.exit(-1)
    finally:
        logger.info(f'Logs have been written into {log_file_path()}')
            



def w3strings_context_work(encoder: W3StringsEncoder, scratch: ScratchFolder, args: CLIArguments):
    input_copy_path = scratch.file_scratch_copy(args.input_path)
    csv_file = encoder.decode(input_copy_path)
    lf_to_crlf(csv_file) # for whatever reason encoder saves the file with unix line endings

    output_csv_path = replace_path_ext(replace_path_dirname(input_copy_path, args.output_dir), ".csv")
    shutil.copy(csv_file, output_csv_path)

    logger.info(f'{args.input_path} has been successfully decoded into {output_csv_path}')


def csv_context_work(encoder: W3StringsEncoder, scratch: ScratchFolder, args: CLIArguments):
    input_copy_path = scratch.file_scratch_copy(args.input_path)
    input_doc = W3StringsCsvDocument(input_copy_path)
    input_doc.read_from_file()

    output_doc_processor = W3StringsCsvDocumentEncodingPreprocessor(input_doc)
    output_doc_path = replace_path_ext(replace_path_dirname(input_copy_path, scratch.folder_path), ".w3stringsx.csv")
    output_doc = output_doc_processor.process_to(output_doc_path)
    output_doc.save_to_file()

    try:
        w3strings_file = encoder.encode(output_doc_path, None)
        langs = ALL_LANGS if args.lang == 'all' else [args.lang]
        for lang in langs:
            copied = os.path.join(args.output_dir, f'{lang}.w3strings')
            logger.info(f'Creating {copied}')
            shutil.copy(w3strings_file, copied)
  
    finally:
        if args.keep_csv:
            logger.info(f'Saving prepared {os.path.basename(output_doc_path)} to {args.output_dir}')
            shutil.copy(output_doc_path, args.output_dir)

    logger.info(f'{args.input_path} has been successfully encoded into w3strings file(s) in {args.output_dir}')


def xml_context_work(args: CLIArguments):
    result = parse_xml_for_str_keys(args.input_path, args.search)
    entries = [W3StringsCsvShortEntry(key) for key in result.keys]

    csv_path = replace_path_ext(replace_path_dirname(args.input_path, args.output_dir), ".en.csv")
    doc = SectionedW3StringsCsvDocument(csv_path)
    doc.append(PARSED_STR_KEYS_CSV_HEADER)
    if result.source == 'config':
        doc.extend_to_config_strings(entries)
    else:
        doc.extend_to_bundle_strings(entries)
    doc.save_to_file()

    logger.info(f'Localisation keys from {args.input_path} have been successfully saved to {csv_path}')


def witcherscript_context_work(args: CLIArguments):   
    keys = sorted(parse_ws_for_str_keys(args.input_path, args.search))
    entries = [W3StringsCsvShortEntry(key) for key in keys]

    csv_path = replace_path_ext(replace_path_dirname(args.input_path, args.output_dir), ".en.csv")
    doc = SectionedW3StringsCsvDocument(csv_path)
    doc.append(PARSED_STR_KEYS_CSV_HEADER)
    doc.extend_to_script_strings(entries)
    doc.save_to_file()

    logger.info(f'Localisation keys from {args.input_path} have been successfully saved to {csv_path}')


def directory_context_work(args: CLIArguments):
    result = parse_directory_for_str_keys(args.input_path, args.search)
    config_entries = [W3StringsCsvShortEntry(key) for key in result.config_keys]
    bundle_entries = [W3StringsCsvShortEntry(key) for key in result.bundle_keys]
    script_entries = [W3StringsCsvShortEntry(key) for key in result.script_keys]
    
    csv_path = replace_path_ext(replace_path_dirname(args.input_path, args.output_dir), ".en.csv")
    doc = SectionedW3StringsCsvDocument(csv_path)
    doc.append(PARSED_STR_KEYS_CSV_HEADER)
    doc.extend_to_config_strings(config_entries)
    doc.extend_to_bundle_strings(bundle_entries)
    doc.extend_to_script_strings(script_entries)
    doc.save_to_file()

    logger.info(f'Localisation keys from {args.input_path} have been successfully saved to {csv_path}')




if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'{e}', file=sys.stderr)
        sys.exit(-1)
