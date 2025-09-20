from __future__ import annotations
import io
from typing import Any, cast, Literal
from xml.etree import ElementTree

from w3stringsx.lib.logging import get_logger
from w3stringsx.lib.utils import guess_file_encoding, sanitize_str_keys, filter_str_keys


__all__ = [
    "parse_xml_for_str_keys",
    "XmlParseResult"
]


logger = get_logger()


_BUNDLED_XML_LOCALIZATION_ATTRIBS: dict[str, list[str]] = {
    # gameplay/abilities
    'effect': ['effectNameLocalisationKey_name', 'effectDescriptionLocalisationKey_name'],
    'skill': ['localisationName', 'localisationDescriptionNotAcquired', 'localisationDescription', 'localisationDescriptionLevel2', 'localisationDescriptionLevel3'],
    # gameplay/items
    'item': ['localisation_key_name', 'localisation_key_description'],
    'recipe': ['localisation_key_name']
}

# A new class, because native ElementTree.Element doesn't have support for easy node parent access
class _ConfigXmlElement:
    element: ElementTree.Element

    parent: Any = None # can't use the same class type for it
    children: list[_ConfigXmlElement]

    display_name: str
    custom_display_name: bool
    custom_names: bool
    non_localized: bool
    non_localized_except_first: bool


    # instantiate using base class object
    def __init__(self, element: ElementTree.Element, parent: Any = None):
        self.element = element
        self.parent = parent
        self.children = []
        self.display_name = ''
        self.custom_display_name = False
        self.custom_names = False
        self.non_localized = False
        self.non_localized_except_first = False

        try:
            self.display_name = element.attrib["displayName"]
            tags = element.attrib["tags"].split(";")
            if "customDisplayName" in tags:
                self.custom_display_name = True
            if "customNames" in tags:
                self.custom_names = True
            if "nonLocalized" in tags:
                self.non_localized = True
            if "nonLocalizedExceptFirst" in tags:
                self.non_localized_except_first = True
        except KeyError:
            pass

        for child in element:
            self.children.append(_ConfigXmlElement(child, self))


    def loc_str_keys(self) -> list[str]:
        if self.display_name == "" or self.non_localized:
            return []
        
        match self.element.tag:
            case "Group":
                keys: list[str] = []

                panel_components = self.display_name.split('.')
                if not self.custom_display_name:
                    keys.extend([f'panel_{dn}' for dn in panel_components])
                else:
                    keys.extend(panel_components)
                
                if "PresetsArray" in [child.element.tag for child in self.children]:
                    keys.append(f'preset_{self.display_name.replace(".", "_")}')

                return keys
            case "Preset":
                return [f'preset_value_{self.display_name}']
            case "Var":
                if not self.custom_display_name:
                    return [f'option_{self.display_name}']
                else:
                    return [self.display_name]
            case "Option":
                var_node = cast(_ConfigXmlElement, self.parent.parent)
                if var_node.non_localized or (var_node.non_localized_except_first and self.element.attrib["id"] != "0"):
                    return []
                elif not var_node.custom_names:
                    return [f'preset_value_{self.display_name}']
                else:
                    return [self.display_name]
            case _:
                return []

    def child_loc_str_keys(self) -> list[str]:
        if len(self.children) == 0:
            return []
        
        keys: list[str] = []
        for child in self.children:
            keys.extend(child.loc_str_keys())
            keys.extend(child.child_loc_str_keys())    

        return keys
    
    def all_loc_str_keys(self) -> list[str]:
        keys: list[str] = []
        keys.extend(self.loc_str_keys())
        keys.extend(self.child_loc_str_keys())
        return keys


def _parse_config_xml_for_str_keys(xml_path: str, search: str) -> list[str]:
    encoding = guess_file_encoding(xml_path)
    logger.info(f"Reading config XML {xml_path}. Detected encoding: {encoding}")

    keys: list[str] = []
    with io.open(xml_path, "r", encoding=encoding) as f:
        xml_str = f.read()
        root = ElementTree.fromstring(xml_str)
        config_xml = _ConfigXmlElement(root)

        keys = filter_str_keys(sanitize_str_keys(config_xml.all_loc_str_keys()), search)

    logger.info(f"Found {len(keys)} string keys in {xml_path}")
    return keys


def _parse_bundled_xml_for_str_keys(xml_path: str, search: str) -> list[str]:
    encoding = guess_file_encoding(xml_path)
    logger.info(f"Reading bundled XML {xml_path}. Detected encoding: {encoding}")

    keys: list[str] = []
    with io.open(xml_path, "r", encoding=encoding) as f:
        for _, elem in ElementTree.iterparse(f, events=["start"]):
            if elem.tag in _BUNDLED_XML_LOCALIZATION_ATTRIBS:
                for attrib in _BUNDLED_XML_LOCALIZATION_ATTRIBS[elem.tag]:
                    keys.append(elem.attrib.get(attrib, ''))

        keys = filter_str_keys(sanitize_str_keys(keys), search)

    logger.info(f"Found {len(keys)} string keys in {xml_path}")
    return keys


def _is_config_xml(xml_path: str) -> bool:
    encoding = guess_file_encoding(xml_path)
    with io.open(xml_path, "r", encoding=encoding) as f:
        _, root = next(ElementTree.iterparse(f, events=["start"]))
        if root.tag == "UserConfig":
            return True
        
    return False


class XmlParseResult:
    source: Literal["config"] | Literal["bundle"]
    keys: list[str]

    def __init__(self, source: Literal["config"] | Literal["bundle"], keys: list[str]) -> None:
        self.source = source
        self.keys = keys

def parse_xml_for_str_keys(xml_path: str, search: str) -> XmlParseResult:
    if _is_config_xml(xml_path):
        source = "config"
        keys = _parse_config_xml_for_str_keys(xml_path, search)
    else:
        source = "bundle"
        keys = _parse_bundled_xml_for_str_keys(xml_path, search)
        
    return XmlParseResult(source, keys)

