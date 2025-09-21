import os
import re
import shutil

from w3stringsx.lib.directory_parsing import *
from w3stringsx.lib.encoder import *
from w3stringsx.lib.localization import *
from w3stringsx.lib.logging import get_logger
from w3stringsx.lib.sectioned_w3strings_csv import *
from w3stringsx.lib.utils import *
from w3stringsx.lib.w3strings_csv import *
from w3stringsx.lib.w3strings_csv_encoding_preprocessor import *
from w3stringsx.lib.ws_parsing import *
from w3stringsx.lib.xml_parsing import *


__all__ = [
    "FileHandlerService"
]


logger = get_logger()


_PARSED_STR_KEYS_CSV_HEADER = W3StringsCsvAttributeComment('mod_id', '?????')

class FileHandlerService:
    def handle_w3strings(self, input_path: str, output_dir: str):
        input_path = self.__validate_file_input_path(input_path, "w3strings", ['.w3strings'])
        output_dir = self.__validate_output_dir(output_dir)
        
        encoder = W3StringsEncoder()
        with ScratchFolder(os.path.dirname(input_path)) as scratch:
            input_copy_path = scratch.file_scratch_copy(input_path)
            csv_file = encoder.decode(input_copy_path)
            lf_to_crlf(csv_file) # for whatever reason encoder saves the file with unix line endings

            output_csv_path = replace_path_ext(replace_path_dirname(input_copy_path, output_dir), ".csv")
            shutil.copy(csv_file, output_csv_path)

        logger.info(f'{input_path} has been successfully decoded into {output_csv_path}')


    def handle_csv(self, input_path: str, output_dir: str, target_langs: list[str], keep_processed_csv: bool):
        input_path = self.__validate_file_input_path(input_path, "CSV", ['.csv'])
        output_dir = self.__validate_output_dir(output_dir)
        target_langs = self.__validate_target_langs(target_langs)

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


    def handle_xml(self, input_path: str, output_dir: str, search: str):
        input_path = self.__validate_file_input_path(input_path, 'XML', ['.xml'])
        output_dir = self.__validate_output_dir(output_dir)
        search = self.__validate_regex_search_string(search)

        result = parse_xml_for_str_keys(input_path, search)
        entries = [W3StringsCsvShortEntry(key) for key in result.keys]

        csv_path = replace_path_ext(replace_path_dirname(input_path, output_dir), ".en.csv")
        doc = SectionedW3StringsCsvDocument(csv_path)
        doc.append(_PARSED_STR_KEYS_CSV_HEADER)
        if result.source == 'config':
            doc.extend_to_config_strings(entries)
        else:
            doc.extend_to_bundle_strings(entries)
        doc.save_to_file()

        logger.info(f'Localisation keys from {input_path} have been successfully saved to {csv_path}')


    def handle_witcherscript(self, input_path: str, output_dir: str, search: str):
        input_path = self.__validate_file_input_path(input_path, 'WitcherScript', ['.ws', '.wss'])
        output_dir = self.__validate_output_dir(output_dir)
        search = self.__validate_regex_search_string(search)

        keys = sorted(parse_ws_for_str_keys(input_path, search))
        entries = [W3StringsCsvShortEntry(key) for key in keys]

        csv_path = replace_path_ext(replace_path_dirname(input_path, output_dir), ".en.csv")
        doc = SectionedW3StringsCsvDocument(csv_path)
        doc.append(_PARSED_STR_KEYS_CSV_HEADER)
        doc.extend_to_script_strings(entries)
        doc.save_to_file()

        logger.info(f'Localisation keys from {input_path} have been successfully saved to {csv_path}')


    def handle_directory(self, input_path: str, output_dir: str, search: str):
        input_path = self.__validate_dir_input_path(input_path)
        output_dir = self.__validate_output_dir(output_dir)
        search = self.__validate_regex_search_string(search)

        result = parse_directory_for_str_keys(input_path, search)
        config_entries = [W3StringsCsvShortEntry(key) for key in result.config_keys]
        bundle_entries = [W3StringsCsvShortEntry(key) for key in result.bundle_keys]
        script_entries = [W3StringsCsvShortEntry(key) for key in result.script_keys]
        
        csv_path = replace_path_ext(replace_path_dirname(input_path, output_dir), ".en.csv")
        doc = SectionedW3StringsCsvDocument(csv_path)
        doc.append(_PARSED_STR_KEYS_CSV_HEADER)
        doc.extend_to_config_strings(config_entries)
        doc.extend_to_bundle_strings(bundle_entries)
        doc.extend_to_script_strings(script_entries)
        doc.save_to_file()

        logger.info(f'Localisation keys from {input_path} have been successfully saved to {csv_path}')


    def __validate_file_input_path(self, input_path: str, file_type_name: str, expected_ext: list[str]) -> str:
        if not os.path.isfile(input_path) or os.path.splitext(input_path)[1] not in expected_ext:
            raise Exception(f"Input path does not lead to an existing {file_type_name} file")
        return os.path.realpath(input_path)
    
    def __validate_dir_input_path(self, input_path: str) -> str:
        if not os.path.isdir(input_path):
            raise Exception(f"Input path does not lead to an existing directory")
        return os.path.realpath(input_path)
    
    def __validate_output_dir(self, output_dir: str) -> str:
        if not os.path.isdir(output_dir):
            if os.path.isfile(output_dir):
                raise Exception("Specified output path points to an existing regular path instead of a directory.")
            if not os.path.isdir(os.path.dirname(output_dir)):
                raise Exception("Parent directory of the specified output path does not exist")

            logger.warning('Specified output directory does not exist. Attempting to create one...')
            try:
                os.mkdir(output_dir)
            except Exception as ex:
                raise Exception('Could not create output directory.', ex)
            logger.warning(f'Directory {output_dir} created successfully')
            
        return os.path.realpath(output_dir)
    
    def __validate_target_langs(self, target_langs: list[str]) -> list[str]:
        if 'all' in target_langs:
            return ALL_LANGS
        else:
            # remvoe duplicates
            target_langs = list(set(target_langs))
            for lang in target_langs:
                if lang not in ALL_LANGS:
                    raise Exception(f"Invalid target language identifier: {lang}")
            return target_langs
        
    def __validate_regex_search_string(self, search: str) -> str:
        if search == '':
            return search

        try:
            re.search(search, "test")
        except Exception as e:
            raise Exception(f'Regex error for search string: {e}')
        
        return search