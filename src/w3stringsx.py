from __future__ import annotations
import argparse
from enum import Enum
import logging
import os
import sys
import traceback

from w3stringsx import W3STRINGSX_VERSION
from w3stringsx.lib.file_handler_service import *
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


class InputPathType(Enum):
    UNSUPPORTED         = 0
    W3STRINGS_FILE      = 1
    CSV_FILE            = 2
    XML_FILE            = 3
    WITCHERSCRIPT_FILE  = 4
    DIRECTORY           = 5

    @staticmethod
    def from_path(path: str) -> InputPathType:
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
    #FIXME allow multiple
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
    if args.output_dir == '':
        # default to the parent directory of the input
        args.output_dir = os.path.dirname(args.input_path)
        logger.info(f'Ouput path set to directory {args.output_dir}')


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

        file_handler = FileHandlerService()
        match InputPathType.from_path(args.input_path):
            case InputPathType.W3STRINGS_FILE:
                file_handler.handle_w3strings(args.input_path, args.output_dir)
            case InputPathType.CSV_FILE:
                file_handler.handle_csv(args.input_path, args.output_dir, [args.lang], args.keep_csv)
            case InputPathType.XML_FILE:
                file_handler.handle_xml(args.input_path, args.output_dir, args.search)
            case InputPathType.WITCHERSCRIPT_FILE:
                file_handler.handle_witcherscript(args.input_path, args.output_dir, args.search)
            case InputPathType.DIRECTORY:
                file_handler.handle_directory(args.input_path, args.output_dir, args.search)
            case _:
                raise Exception(f'Unsupported file type: {os.path.basename(args.input_path)}')
                        
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        sys.exit(-1)
    finally:
        logger.info(f'Logs have been written into {log_file_path()}')

    #TODO make sure user sees logs if there were errors


if __name__ == '__main__':
    main()

