import os
import shutil

from w3stringsx_lib.logging import get_logger
from w3stringsx_lib.utils import replace_path_dirname, replace_path_ext, lf_to_crlf
from w3stringsx_lib.w3strings_csv import W3StringsCsvDocument
from w3stringsx_lib.w3strings_csv_encoding_preprocessor import W3StringsCsvDocumentEncodingPreprocessor
from w3stringsx_svc.validators import validate_file_input_path, validate_output_dir, validate_lang_list
from w3stringsx_svc.w3strings_encoder import W3StringsEncoder
from w3stringsx_svc.scratch_folder_service import ScratchFolderService


__all__ = [
    "W3StringsManagerService"
]


logger = get_logger()


class W3StringsManagerService:
    def __init__(self, 
        encoder: W3StringsEncoder, 
        scratch: ScratchFolderService
    ) -> None:
        self.__encoder = encoder
        self.__scratch = scratch

    def decode_w3strings_to_csv(self, input_path: str, output_dir: str):
        input_path = validate_file_input_path(input_path, "w3strings", ['.w3strings'])
        output_dir = validate_output_dir(output_dir)
        
        input_copy_path = self.__scratch.get().file_scratch_copy(input_path)
        csv_file = self.__encoder.decode(input_copy_path)
        lf_to_crlf(csv_file) # for whatever reason encoder saves the file with unix line endings

        output_csv_path = replace_path_ext(replace_path_dirname(input_copy_path, output_dir), ".csv")
        shutil.copy(csv_file, output_csv_path)

        logger.info(f'{input_path} has been successfully decoded into {output_csv_path}')


    def encode_w3strings_from_csv(self, input_path: str, output_dir: str, target_langs: list[str], keep_processed_csv: bool):
        input_path = validate_file_input_path(input_path, "CSV", ['.csv'])
        output_dir = validate_output_dir(output_dir)
        target_langs = validate_lang_list(target_langs)

        input_copy_path = self.__scratch.get().file_scratch_copy(input_path)
        input_doc = W3StringsCsvDocument(input_copy_path)
        input_doc.read_from_file()

        output_doc_processor = W3StringsCsvDocumentEncodingPreprocessor(input_doc)
        output_doc_path = replace_path_ext(replace_path_dirname(input_copy_path, self.__scratch.get().folder_path), ".w3stringsx.csv")
        output_doc = output_doc_processor.process_to(output_doc_path)
        output_doc.save_to_file()

        try:
            w3strings_file = self.__encoder.encode(output_doc_path, None)
            for lang in target_langs:
                copied = os.path.join(output_dir, f'{lang}.w3strings')
                logger.info(f'Creating {copied}')
                shutil.copy(w3strings_file, copied)
    
        finally:
            if keep_processed_csv:
                logger.info(f'Saving prepared {os.path.basename(output_doc_path)} to {output_dir}')
                shutil.copy(output_doc_path, output_dir)

        logger.info(f'{input_path} has been successfully encoded into w3strings file(s) in {output_dir}')