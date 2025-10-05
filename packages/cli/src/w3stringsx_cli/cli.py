import argparse
import os

from w3stringsx_lib.localization import ALL_LANGS
from w3stringsx_lib.logging import get_logger


__all__ = [
    "CLIArguments",
    "make_cli",
    "preprocess_cli_args"
]


logger = get_logger()


class CLIArguments:
    input_path: str
    output_dir: str
    langs: list[str]
    keep_csv: bool
    search: str
    warn_level: int


W3STRINGSX_VERSION = '2.0.0' #TODO replace with data taken from build system

def make_cli() -> CLIArguments:
    parser = argparse.ArgumentParser(
        prog='w3stringsx.exe',
        description=f'w3stringsx v{W3STRINGSX_VERSION}\n'
                    'https://github.com/SpontanCombust/w3stringsx\n\n'
                    'Script acting as an alternative CLI frontend for w3strings encoder '
                    'while also providing additional functionalities to make working with localized Witcher 3 content easier and faster.',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='remarks:\n'
                '  * --language and --keep-csv arguments apply only to CSV file context\n'
                '  * --search option applies only to XML, WitcherScript and directory contexts'
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
        help=f'set the target encoding language, argument may be passed multiple times; omitting this argument will generate all possible variants; available: {ALL_LANGS}',
        default=[],
        dest='langs', action='append')

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
    cli.langs = list(args.langs)
    cli.keep_csv = bool(args.keep_csv)
    cli.search = str(args.search)

    try:
        cli.warn_level = int(args.warn_level)
    except ValueError:
        raise Exception('Invalid logging level value')

    return cli


def preprocess_cli_args(args: CLIArguments):
    args.input_path = os.path.realpath(args.input_path)

    if args.output_dir == '':
        # default to the parent directory of the input
        args.output_dir = os.path.dirname(args.input_path)
        logger.info(f'Ouput path set to directory {args.output_dir}')

    if len(args.langs) == 0:
        args.langs = ALL_LANGS