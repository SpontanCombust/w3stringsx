import os
import shutil

from w3stringsx.lib.encoder import W3StringsEncoder
from w3stringsx.lib.logging import get_logger
from w3stringsx.lib.utils import *
from w3stringsx.lib.w3strings_csv import W3StringsCsvDocument
from w3stringsx.lib.w3strings_csv_encoding_preprocessor import W3StringsCsvDocumentEncodingPreprocessor
from w3stringsx.svc.validators import *


__all__ = [
    "W3StringsService"
]


logger = get_logger()


class W3StringsService:
    def decode_w3strings_to_csv(self, input_path: str, output_dir: str):
        input_path = validate_file_input_path(input_path, "w3strings", ['.w3strings'])
        output_dir = validate_output_dir(output_dir)
        
        encoder = W3StringsEncoder()
        with ScratchFolder(os.path.dirname(input_path)) as scratch:
            input_copy_path = scratch.file_scratch_copy(input_path)
            csv_file = encoder.decode(input_copy_path)
            lf_to_crlf(csv_file) # for whatever reason encoder saves the file with unix line endings

            output_csv_path = replace_path_ext(replace_path_dirname(input_copy_path, output_dir), ".csv")
            shutil.copy(csv_file, output_csv_path)

        logger.info(f'{input_path} has been successfully decoded into {output_csv_path}')


    def encode_w3strings_from_csv(self, input_path: str, output_dir: str, target_langs: list[str], keep_processed_csv: bool):
        input_path = validate_file_input_path(input_path, "CSV", ['.csv'])
        output_dir = validate_output_dir(output_dir)
        target_langs = validate_target_langs(target_langs)

        encoder = W3StringsEncoder()
        with ScratchFolder(os.path.dirname(input_path)) as scratch:
            input_copy_path = scratch.file_scratch_copy(input_path)
            input_doc = W3StringsCsvDocument(input_copy_path)
            input_doc.read_from_file()

            output_doc_processor = W3StringsCsvDocumentEncodingPreprocessor(input_doc)
            output_doc_path = replace_path_ext(replace_path_dirname(input_copy_path, scratch.folder_path), ".w3stringsx.csv")
            output_doc = output_doc_processor.process_to(output_doc_path)
            output_doc.save_to_file()

            try:
                w3strings_file = encoder.encode(output_doc_path, None)
                for lang in target_langs:
                    copied = os.path.join(output_dir, f'{lang}.w3strings')
                    logger.info(f'Creating {copied}')
                    shutil.copy(w3strings_file, copied)
        
            finally:
                if keep_processed_csv:
                    logger.info(f'Saving prepared {os.path.basename(output_doc_path)} to {output_dir}')
                    shutil.copy(output_doc_path, output_dir)

        logger.info(f'{input_path} has been successfully encoded into w3strings file(s) in {output_dir}')