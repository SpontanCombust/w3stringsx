"""
w3strings encoder handling
"""

import os
import subprocess

from w3stringsx import W3STRINGSX_PKG_ROOT
from w3stringsx.lib.logging import get_logger

__all__ = [
    "W3StringsEncoder"
]


logger = get_logger()


class W3StringsEncoder:
    exe_path: str

    def __init__(self):
        # TODO cache encoder path
        logger.info('Looking for w3strings encoder in w3stringsx\'s directory...')
        self.exe_path = os.path.join(os.path.dirname(W3STRINGSX_PKG_ROOT), 'w3strings.exe')
        
        if not os.path.exists(self.exe_path):
            logger.info('w3strings encoder not found in w3stringsx\'s directory. Checking the PATH environment variable...')
            # check PATH
            for path in os.environ["PATH"].split(';'):
                encoder_path = os.path.join(path, 'w3strings.exe')
                if os.path.exists(encoder_path):
                    self.exe_path = encoder_path
                    break

        if os.path.exists(self.exe_path):
            logger.info(f'Found w3strings encoder: {self.exe_path}')
        else:
            raise Exception('w3strings encoder couldn\'t be found')


    def execute(self, cmd: str):
        cmd = f'"{self.exe_path}" {cmd}'

        logger.warning('Executing command:')
        logger.warning(cmd)

        # we ignore stderr, because it contains only the thread panic message without any information that is helpful to us
        output = subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        logger.info('=' * 100)
        lines = output.stdout.split('\n')
        for line in lines:
            self.log_encoder_output(line)
        logger.info('=' * 100)
  
        if output.returncode != 0:
            raise Exception('Process exited with an error')

    # Returns the path to decoded file
    def decode(self, w3strings_path: str) -> str:
        logger.info(f'Decoding {w3strings_path}...')
        self.execute(f'-d "{w3strings_path}"')
        return w3strings_path + '.csv' 

    # Returns the path to encoded file
    def encode(self, csv_path: str, id_space: int | None) -> str:
        cmd = f'-e "{csv_path}" '
        if id_space is None:
            # TODO always use this flag and do checks only on w3stringsx's side
            DISABLE_ID_CHECK_FLAG = '--force-ignore-id-space-check-i-know-what-i-am-doing'
            logger.warning(f'Disabling ID check in the encoder because of the existence of entries outside of a single mod ID range')
            cmd += DISABLE_ID_CHECK_FLAG
        else:
            cmd += f'-i {id_space}'

        logger.info(f'Encoding {csv_path}...')
        self.execute(cmd)

        w3strings_path = csv_path + '.w3strings'
        ws_path = w3strings_path + '.ws'

        if os.path.exists(ws_path):
            logger.info(f'Removing {ws_path}')
            os.remove(ws_path)

        return w3strings_path
    

    def log_encoder_output(self, line: str):
        if line.startswith('INFO'):
            logger.info(line[7:])
        elif line.startswith('WARN'):
            logger.warning(line[7:])
        elif line.startswith('ERROR'):
            logger.error(line[8:])
        elif len(line) > 0:
            logger.info(line)


