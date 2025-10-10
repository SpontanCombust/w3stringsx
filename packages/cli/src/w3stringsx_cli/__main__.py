from __future__ import annotations
from enum import Enum
import os
import sys
import traceback

from w3stringsx_cli.cli import make_cli, preprocess_cli_args
from w3stringsx_lib.logging import get_logger, init_logger, get_log_file_path
from w3stringsx_svc.string_key_discovery_service import StringKeyDiscoveryService
from w3stringsx_svc.w3strings_service import W3StringsService


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
                

def main():
    # path outside of the .pyz archive
    W3STRINGSX_APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    init_logger(W3STRINGSX_APP_DIR)

    try:
        # if -h flag is set it will forcefully exit the function
        args = make_cli()
        preprocess_cli_args(args)

        match InputPathType.from_path(args.input_path):
            case InputPathType.W3STRINGS_FILE:
                w3strings_svc = W3StringsService(W3STRINGSX_APP_DIR)
                w3strings_svc.decode_w3strings_to_csv(args.input_path, args.output_dir)
            case InputPathType.CSV_FILE:
                w3strings_svc = W3StringsService(W3STRINGSX_APP_DIR)
                w3strings_svc.encode_w3strings_from_csv(args.input_path, args.output_dir, args.langs, args.keep_csv)
            case InputPathType.XML_FILE:
                discovery_svc = StringKeyDiscoveryService()
                discovery_svc.discover_str_keys_in_xml(args.input_path, args.output_dir, args.search)
            case InputPathType.WITCHERSCRIPT_FILE:
                discovery_svc = StringKeyDiscoveryService()
                discovery_svc.discover_str_keys_in_witcherscript(args.input_path, args.output_dir, args.search)
            case InputPathType.DIRECTORY:
                discovery_svc = StringKeyDiscoveryService()
                discovery_svc.discover_str_keys_in_directory(args.input_path, args.output_dir, args.search)
            case _:
                raise Exception(f'Unsupported file type: {os.path.basename(args.input_path)}')
                        
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        sys.exit(-1)
    finally:
        logger.info(f'Logs have been written into {get_log_file_path()}')


if __name__ == '__main__':
    main()
