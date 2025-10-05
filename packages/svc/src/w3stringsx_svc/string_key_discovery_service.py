from w3stringsx_lib.directory_parsing import parse_directory_for_str_keys
from w3stringsx_lib.logging import get_logger
from w3stringsx_lib.sectioned_w3strings_csv import SectionedW3StringsCsvDocument
from w3stringsx_lib.utils import replace_path_dirname, replace_path_ext
from w3stringsx_lib.w3strings_csv import W3StringsCsvAttributeComment, W3StringsCsvShortEntry
from w3stringsx_lib.ws_parsing import parse_ws_for_str_keys
from w3stringsx_lib.xml_parsing import parse_xml_for_str_keys
from w3stringsx_svc.validators import validate_dir_input_path, validate_file_input_path, validate_output_dir, validate_regex_search_string


__all__ = [
    "StringKeyDiscoveryService"
]


logger = get_logger()


_PARSED_STR_KEYS_CSV_HEADER = W3StringsCsvAttributeComment('mod_id', '?????')

class StringKeyDiscoveryService:
    def discover_str_keys_in_xml(self, input_path: str, output_dir: str, search: str):
        input_path = validate_file_input_path(input_path, 'XML', ['.xml'])
        output_dir = validate_output_dir(output_dir)
        search = validate_regex_search_string(search)

        result = parse_xml_for_str_keys(input_path, search)
        entries = [W3StringsCsvShortEntry(key) for key in result.keys]

        csv_path = replace_path_ext(replace_path_dirname(input_path, output_dir), ".en.csv")
        doc = SectionedW3StringsCsvDocument(csv_path)
        doc.append(_PARSED_STR_KEYS_CSV_HEADER)
        if result.source == 'config':
            doc.extend_to_config_strings(entries)
        else:
            doc.extend_to_bundle_strings(entries)
        doc.save_to_file()

        logger.info(f'Localisation keys from {input_path} have been successfully saved to {csv_path}')


    def discover_str_keys_in_witcherscript(self, input_path: str, output_dir: str, search: str):
        input_path = validate_file_input_path(input_path, 'WitcherScript', ['.ws', '.wss'])
        output_dir = validate_output_dir(output_dir)
        search = validate_regex_search_string(search)

        keys = sorted(parse_ws_for_str_keys(input_path, search))
        entries = [W3StringsCsvShortEntry(key) for key in keys]

        csv_path = replace_path_ext(replace_path_dirname(input_path, output_dir), ".en.csv")
        doc = SectionedW3StringsCsvDocument(csv_path)
        doc.append(_PARSED_STR_KEYS_CSV_HEADER)
        doc.extend_to_script_strings(entries)
        doc.save_to_file()

        logger.info(f'Localisation keys from {input_path} have been successfully saved to {csv_path}')


    def discover_str_keys_in_directory(self, input_path: str, output_dir: str, search: str):
        input_path = validate_dir_input_path(input_path)
        output_dir = validate_output_dir(output_dir)
        search = validate_regex_search_string(search)

        result = parse_directory_for_str_keys(input_path, search)
        config_entries = [W3StringsCsvShortEntry(key) for key in result.config_keys]
        bundle_entries = [W3StringsCsvShortEntry(key) for key in result.bundle_keys]
        script_entries = [W3StringsCsvShortEntry(key) for key in result.script_keys]
        
        csv_path = replace_path_ext(replace_path_dirname(input_path, output_dir), ".en.csv")
        doc = SectionedW3StringsCsvDocument(csv_path)
        doc.append(_PARSED_STR_KEYS_CSV_HEADER)
        doc.extend_to_config_strings(config_entries)
        doc.extend_to_bundle_strings(bundle_entries)
        doc.extend_to_script_strings(script_entries)
        doc.save_to_file()

        logger.info(f'Localisation keys from {input_path} have been successfully saved to {csv_path}')
