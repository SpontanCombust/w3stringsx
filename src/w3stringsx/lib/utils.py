"""
Various utility classes and functions
"""

import io
import os
import re
import shutil

from w3stringsx.lib.logging import get_logger

__all__ = [
    "ScratchFolder",
    "lf_to_crlf",
    "maybeisfile",
    "guess_file_encoding",
    "str_key_list_difference",
    "sanitize_str_keys",
    "filter_str_keys",
]


logger = get_logger()


# Because encoder ALWAYS puts output in the same directory as input before we are able to move it 
# we first need to create a temporary folder in which we'll execute the commands.
# This way no files will be overwritten without user's consent
class ScratchFolder:
    folder_path: str

    def __init__(self, work_dir: str):
        if not os.path.exists(work_dir):
            raise Exception("Working directory for the scratch folder does not exist")
        elif not os.path.isdir(work_dir):
            raise Exception("Working directory for the scratch folder is not a directory")

        self.folder_path = os.path.join(work_dir, '.tmp.w3stringsx')
        if not os.path.exists(self.folder_path):
            logger.info(f'Creating scratch folder {self.folder_path}')
            os.mkdir(self.folder_path)


    def __del__(self):
        logger.info(f'Removing scratch folder {self.folder_path}')
        shutil.rmtree(self.folder_path)

    def file_scratch_copy(self, input_path: str) -> str:
        input_basename = os.path.basename(input_path)
        copy_path = os.path.join(self.folder_path, input_basename)

        if not os.path.exists(copy_path):
            shutil.copy(input_path, copy_path)
        
        return copy_path
    
"""
Converts new line endings in the file from Unix style to Windows style 
"""
def lf_to_crlf(file_path: str):
    encoding = guess_file_encoding(file_path)
    with io.open(file_path, mode="r+", encoding=encoding) as f:
        data = f.read()
        data.replace('\n', '\r\n')
        f.seek(0)
        f.write(data)
        f.truncate()


"""
Returns whether this path that may not exist could point to a file
"""
def maybeisfile(path:str) -> bool:
    return os.path.splitext(path)[1] != ''


def guess_file_encoding(path: str) -> str:
    with io.open(path, mode="rb") as f:
        header = f.read(3)
        if header.startswith(b'\xFF\xFE'):
            return "UTF-16-LE"
        elif header.startswith(b'\xFE\xFF'):
            return "UTF-16-BE"
        elif header.startswith(b'\xEF\xBB\xBF'):
            return "UTF-8-SIG"

    return "UTF-8"

"""
Set operation, but done to preserve the order of lhs
"""
def str_key_list_difference(lhs: list[str], rhs: list[str]) -> list[str]:
    rhs_set = set(rhs)
    return [k for k in lhs if k not in rhs_set]

"""
Remove empty and duplicated keys while preserving the order of first appearance
"""
def sanitize_str_keys(keys: list[str]) -> list[str]:
    key_set = set[str]()  # using set for fast lookup
    result = list[str]()

    for k in keys:
        if k not in key_set and k != "":
            key_set.add(k)
            result.append(k)

    return result

def filter_str_keys(keys: list[str], search: str) -> list[str]:
    return list(filter(lambda k: re.search(search, k) is not None, keys))