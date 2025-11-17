from dataclasses import dataclass
import io
from typing import Iterable


_STRINGS_DB_EXPORT_CSV_HEADER = "ID;RESOURCE;PROPERTY;VOICEOVER;KEY;BR;CZ;RU;AR;TR;CN;PL;IT;FR;DE;ZH;ESMX;EN;KR;ES;JP;HU"

@dataclass
class StringsDbExportCsvLine:
    id: int
    resource: str
    property: str = ''
    voiceover: str | None = None
    key: str | None = None
    br: str | None = None
    cz: str | None = None
    ru: str | None = None
    ar: str | None = None
    tr: str | None = None
    cn: str | None = None
    pl: str | None = None
    it: str | None = None
    fr: str | None = None
    de: str | None = None
    zh: str | None = None
    esmx: str | None = None
    en: str | None = None
    kr: str | None = None
    es: str | None = None
    jp: str | None = None
    hu: str | None = None

    def __str__(self) -> str:
        return ';'.join([
            str(self.id),
            self.resource,
            self.property,
            self.voiceover or '',
            self.key or '',
            self.br or '',
            self.cz or '',
            self.ru or '',
            self.ar or '',
            self.tr or '',
            self.cn or '',
            self.pl or '',
            self.it or '',
            self.fr or '',
            self.de or '',
            self.de or '',
            self.zh or '',
            self.esmx or '',
            self.en or '',
            self.kr or '',
            self.es or '',
            self.jp or '',
            self.hu or ''
        ])


class StringsDbExportCsvDocument:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.lines: list[StringsDbExportCsvLine] = []

    def append(self, line: StringsDbExportCsvLine):
        self.lines.append(line)

    def extend(self, lines: Iterable[StringsDbExportCsvLine]):
        self.lines.extend(lines)

    def save_to_file(self):
        with io.open(self.file_path, mode='w', encoding='UTF-8') as file:
            lines_as_strs = [_STRINGS_DB_EXPORT_CSV_HEADER + '\n'] + [str(row) + '\n' for row in self.lines]
            file.writelines(lines_as_strs)