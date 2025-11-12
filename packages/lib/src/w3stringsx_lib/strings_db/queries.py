from dataclasses import dataclass


@dataclass
class LatestStringsWithInfo:
    string_id: int
    lang: int
    version: int
    text: str
    resource: str
    property_name: str
    voiceover_name: str | None
    string_key: str | None

@dataclass
class LatestStringsWithInfoShort:
    string_id: int
    lang: int
    string_key: str | None
    text: str