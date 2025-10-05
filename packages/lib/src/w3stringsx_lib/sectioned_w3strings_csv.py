from typing import Iterable

from w3stringsx_lib.w3strings_csv import W3StringsCsvDocument, W3StringsCsvAttributeComment, W3StringsCsvDocumentLine


__all__ = [
    "SectionedW3StringsCsvDocument"
]


class SectionedW3StringsCsvDocument(W3StringsCsvDocument):
    __SECTION_COMMENT_KEY = "section"
    __SECTION_COMMENT_CONFIG = W3StringsCsvAttributeComment(__SECTION_COMMENT_KEY, "configuration")
    __SECTION_COMMENT_BUNDLE = W3StringsCsvAttributeComment(__SECTION_COMMENT_KEY, "bundles")
    __SECTION_COMMENT_SCRIPTS = W3StringsCsvAttributeComment(__SECTION_COMMENT_KEY, "scripts")

    def __init__(self, file_path: str):
        super().__init__(file_path)

    def extend_to_script_strings(self, lines: Iterable[W3StringsCsvDocumentLine]):
        self.__extend_to_section(lines, self.__SECTION_COMMENT_SCRIPTS)

    def extend_to_config_strings(self, lines: Iterable[W3StringsCsvDocumentLine]):
        self.__extend_to_section(lines, self.__SECTION_COMMENT_CONFIG)

    def extend_to_bundle_strings(self, lines: Iterable[W3StringsCsvDocumentLine]):
        self.__extend_to_section(lines, self.__SECTION_COMMENT_BUNDLE)

    def __extend_to_section(self, lines: Iterable[W3StringsCsvDocumentLine], section: W3StringsCsvAttributeComment):
        insert_idx = self.__get_section_insertion_index(section)
        self.lines = self.lines[:insert_idx] + list(lines) + self.lines[insert_idx:]

    def __get_section_insertion_index(self, section: W3StringsCsvAttributeComment) -> int:
        insert_idx = -1
        try:
            insert_idx = self.lines.index(section) + 1
        except ValueError:
            self.append(section)
            insert_idx = len(self.lines)

        while insert_idx < len(self.lines):
            line = self.lines[insert_idx]
            if isinstance(line, W3StringsCsvAttributeComment) and line.key == self.__SECTION_COMMENT_KEY:
                break
            insert_idx += 1

        return insert_idx
        
