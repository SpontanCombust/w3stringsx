import os
import sys
import traceback

from w3stringsx_lib.logging import init_logger, get_log_file_path
from w3stringsx_cli.cli import cli_main

def main():
    # path outside of the .pyz archive
    W3STRINGSX_APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    logger = init_logger(W3STRINGSX_APP_DIR)

    try:
        cli_main(W3STRINGSX_APP_DIR)                
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        sys.exit(-1)
    finally:
        logger.info(f'Logs have been written into {get_log_file_path()}')


if __name__ == '__main__':
    main()
