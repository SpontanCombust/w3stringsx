from dataclasses import dataclass
    

@dataclass
class Languages:
    id: int
    lang: str
    fallback: int

@dataclass
class StringInfo:
    string_id: int
    resource: str
    property_name: str
    voiceover_name: str | None = None
    string_key: str | None = None

@dataclass
class Strings:
    string_id: int
    lang: int
    version: int
    text: str | None = None
