import io
import os
from typing import Iterable

from w3stringsx_lib.logging import get_logger
from w3stringsx_lib.utils import guess_file_encoding
from w3stringsx_lib.localization import StringId


__all__ = [
    "W3StringsCsvCompleteEntry",
    "W3StringsCsvShortEntry",
    "W3StringsCsvPlainComment",
    "W3StringsCsvAttributeComment",
    "W3StringsCsvDocumentLine",
    "W3StringsCsvDocument"
]


logger = get_logger()


class W3StringsCsvCompleteEntry:
    id: StringId
    key_hex: str
    key_str: str
    text: str

    def __init__(self, id: StringId, key_hex: str, key_str: str, text: str = "MISSING_LOCALISATION") -> None:
        self.id = id
        self.key_hex = key_hex
        self.key_str = key_str
        self.text = text

    def __str__(self) -> str:
        return '|'.join([
            str(self.id).rjust(10, ' '),
            self.key_hex.rjust(8, ' '),
            self.key_str,
            self.text
        ])
        
class W3StringsCsvShortEntry:
    key_str: str
    text: str

    def __init__(self, key_str: str, text: str = "MISSING_LOCALISATION"):
        self.key_str = key_str
        self.text = text

    def __str__(self) -> str:
        return '|'.join([
            self.key_str,
            self.text
        ])

    def into_complete(self, id: StringId, key_hex: str = '') -> W3StringsCsvCompleteEntry:
        return W3StringsCsvCompleteEntry(
            id,
            key_hex,
            self.key_str,
            self.text
        )

class W3StringsCsvPlainComment:
    comment_text: str

    def __init__(self, line: str):
        self.comment_text = line

    def __str__(self) -> str:
        return f';{self.comment_text}'
        
class W3StringsCsvAttributeComment:
    key: str
    value: str

    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value

    def __str__(self) -> str:
        return f";{self.key}={self.value}"
    
class W3StringsCsvEmptyLine:
    def __str__(self) -> str:
        return ""
    
W3StringsCsvDocumentLine = W3StringsCsvCompleteEntry | W3StringsCsvShortEntry | W3StringsCsvPlainComment | W3StringsCsvAttributeComment | W3StringsCsvEmptyLine


class W3StringsCsvDocument:
    file_path: str
    lines: list[W3StringsCsvDocumentLine]

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lines = []

    def append(self, line: W3StringsCsvDocumentLine):
        self.lines.append(line)

    def extend(self, lines: Iterable[W3StringsCsvDocumentLine]):
        self.lines.extend(lines)

    def pop(self, index: int = -1):
        self.lines.pop(index)

    def insert(self, index: int, line: W3StringsCsvDocumentLine):
        self.lines.insert(index, line)

    def clear(self):
        self.lines.clear()

    def swap_lines(self, line1_idx: int, line2_idx: int):
        line_range = range(0, len(self.lines))
        if line1_idx in line_range and line2_idx in line_range:
            line1 = self.lines[line1_idx]
            self.lines[line1_idx] = self.lines[line2_idx]
            self.lines[line2_idx] = line1

    def read_from_file(self):
        if not os.path.exists(self.file_path):
            logger.critical("File %s does not exist and cannot be read", self.file_path)
            return

        encoding = guess_file_encoding(self.file_path)
        logger.info('Reading %s. Detected encoding: %s', self.file_path, encoding)

        self.lines = []
        parsed_with_errors = False
        with io.open(self.file_path, mode='r', encoding=encoding) as file:
            for (line_num, line) in enumerate(file.readlines()):
                try:
                    parsed = W3StringsCsvDocument._read_line(line)
                    if parsed is not None:
                        self.lines.append(parsed)
                except Exception as ex:
                    logger.error("Parsing error at line %d: %s", line_num + 1, ex)
                    parsed_with_errors = True

        if parsed_with_errors:
            raise Exception("Errors occured while reading the file")

    def save_to_file(self):
        with io.open(self.file_path, mode='w', encoding='UTF-8') as file:
            lines_as_strs = [str(line) + '\n' for line in self.lines]
            file.writelines(lines_as_strs)
            logger.info("Saved CSV document to %s", self.file_path)
    
    @staticmethod
    def _read_line(line: str) -> W3StringsCsvDocumentLine:
        line = line.strip()
        if len(line) == 0:
            return W3StringsCsvEmptyLine()
        
        if line.startswith(';'):
            return W3StringsCsvDocument._read_comment(line)
        else:
            return W3StringsCsvDocument._read_string_entry(line)

    @staticmethod 
    def _read_string_entry(entry_line: str) -> W3StringsCsvCompleteEntry | W3StringsCsvShortEntry:
        split = entry_line.split('|')
            
        if len(split) == 2:
            return W3StringsCsvShortEntry(
                split[0], 
                split[1]
            )
        elif len(split) == 4:
            id_num: int
            try:
                id_num = int(split[0])
            except ValueError:
                raise Exception('Failed to parse id column to a number')

            return W3StringsCsvCompleteEntry(
                StringId(id_num),
                split[1],
                split[2],
                split[3]
            )
        else:
            raise Exception(f'Invalid column count. Expected 2 or 4, got {len(split)}')

    @staticmethod
    def _read_comment(comment_line: str) -> W3StringsCsvPlainComment | W3StringsCsvAttributeComment:
        if not comment_line.count('=') == 1:
            return W3StringsCsvPlainComment(comment_line[1:])
        
        stripped_line = comment_line[1:].replace(' ', '')
        split = stripped_line.split('=')
        return W3StringsCsvAttributeComment(split[0], split[1])
        