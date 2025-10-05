import os
import re

from w3stringsx_lib.localization import ALL_LANGS
from w3stringsx_lib.logging import get_logger


__all__ = [
    "validate_file_input_path",
    "validate_dir_input_path",
    "validate_output_dir",
    "validate_target_langs",
    "validate_regex_search_string"
]


logger = get_logger()


def validate_file_input_path(input_path: str, file_type_name: str, expected_ext: list[str]) -> str:
        if not os.path.isfile(input_path) or os.path.splitext(input_path)[1] not in expected_ext:
            raise Exception(f"Input path does not lead to an existing {file_type_name} file")
        return os.path.realpath(input_path)
    
def validate_dir_input_path(input_path: str) -> str:
    if not os.path.isdir(input_path):
        raise Exception("Input path does not lead to an existing directory")
    return os.path.realpath(input_path)

def validate_output_dir(output_dir: str) -> str:
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

def validate_target_langs(target_langs: list[str]) -> list[str]:
    # remove duplicates
    target_langs = list(set(target_langs))
    for lang in target_langs:
        if lang not in ALL_LANGS:
            raise Exception(f"Invalid target language identifier: {lang}")
    return target_langs
    
def validate_regex_search_string(search: str) -> str:
    if search == '':
        return search

    try:
        re.search(search, "test")
    except Exception as e:
        raise Exception(f'Regex error for search string: {e}')
    
    return search