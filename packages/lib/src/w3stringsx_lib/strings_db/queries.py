from dataclasses import dataclass


@dataclass
class LatestStringsWithInfoRow:
    string_id: int
    lang: int | None
    version: int | None
    text: str | None
    resource: str
    property_name: str
    voiceover_name: str | None
    string_key: str | None

@dataclass
class LatestStringsWithInfoShortRow:
    string_id: int
    lang: int | None
    string_key: str | None
    text: str | None