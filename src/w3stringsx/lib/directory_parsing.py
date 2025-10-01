import os

from w3stringsx.lib.utils import sanitize_str_keys, str_key_list_difference
from w3stringsx.lib.ws_parsing import parse_ws_for_str_keys
from w3stringsx.lib.xml_parsing import parse_xml_for_str_keys


__all__ = [
    "parse_directory_for_str_keys",
    "DirectoryParseResult"
]


class DirectoryParseResult:
    config_keys: list[str]
    bundle_keys: list[str]
    script_keys: list[str]

    def __init__(self) -> None:
        self.config_keys = []
        self.bundle_keys = []
        self.script_keys = []

    def sanitize(self):
        self.config_keys = sanitize_str_keys(self.config_keys)
        
        self.bundle_keys = sorted(sanitize_str_keys(self.bundle_keys))
        # remove keys that appear across multiple source types
        self.bundle_keys = str_key_list_difference(self.bundle_keys, self.config_keys)

        self.script_keys = sorted(sanitize_str_keys(self.script_keys))
        self.script_keys = str_key_list_difference(self.script_keys, self.config_keys)
        self.script_keys = str_key_list_difference(self.script_keys, self.bundle_keys)

def parse_directory_for_str_keys(directory_path: str, search: str) -> DirectoryParseResult:
    if not os.path.isdir(directory_path):
        raise Exception(f"{directory_path} is not an existing directory")
    
    result = DirectoryParseResult()

    for root, _, files in os.walk(directory_path):
        for file in files:
            path = os.path.join(root, file)
            if not os.path.isdir(path):
                _, ext = os.path.splitext(path)
                match ext:
                    case '.ws' | '.wss':
                        result.script_keys.extend(parse_ws_for_str_keys(path, search))
                    case '.xml':
                        xml_result = parse_xml_for_str_keys(path, search)
                        if xml_result.source == 'config':
                            result.config_keys.extend(xml_result.keys)
                        else:
                            result.bundle_keys.extend(xml_result.keys)
                    case _:
                        pass
    
    result.sanitize()

    return result
