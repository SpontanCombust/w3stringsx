"""
w3strings encoder handling
"""

import os
import subprocess

from w3stringsx_lib.logging import get_logger
from w3stringsx_svc.w3strings_encoder_locator import W3StringsEncoderLocator


__all__ = [
    "W3StringsEncoder"
]


logger = get_logger()


class W3StringsEncoder:    
    encoder_path: str

    def __init__(self, encoder_locator: W3StringsEncoderLocator):
        encoder_path = encoder_locator.find()

        if encoder_path is None:
            raise Exception('w3strings encoder couldn\'t be found')
        
        self.encoder_path = encoder_path


    def execute(self, cmd: str):
        cmd = f'"{self.encoder_path}" {cmd}'

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
            DISABLE_ID_CHECK_FLAG = '--force-ignore-id-space-check-i-know-what-i-am-doing'
            logger.warning('Disabling ID check in the w3strings encoder')
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
    