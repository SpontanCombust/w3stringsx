import os

from w3stringsx_lib.logging import get_logger
from w3stringsx_lib.localization import ALL_LANGS, ALL_LANGS_META_MAP, StringId, StringIdSpace, StringIdSpaceIterator
from w3stringsx_lib.w3strings_csv import W3StringsCsvDocument, W3StringsCsvPlainComment, W3StringsCsvAttributeComment, W3StringsCsvCompleteEntry, W3StringsCsvShortEntry


__all__ = [
    "W3StringsCsvDocumentEncodingPreprocessor"
]


logger = get_logger()


_MOD_ID_COMMENT_KEY = "mod_id"
_MOD_ID_LEGACY_COMMENT_KEY = "mod_id_legacy"

"""
Translates CSVs to a form acceptable for the w3strings encoder
"""
class W3StringsCsvDocumentEncodingPreprocessor:
    _doc: W3StringsCsvDocument
    _title_lang: str | None
    _header_meta_lang: str | None

    def __init__(self, doc: W3StringsCsvDocument) -> None:
        self._doc = doc
        self._title_lang = None
        self._header_meta_lang = None

    def process_to(self, output_file_path: str) -> W3StringsCsvDocument:
        self._read_input_doc_title()
        self._read_input_doc_header()

        output_doc = W3StringsCsvDocument(output_file_path)
        self._generate_output_header(output_doc)
        self._generate_output_content(output_doc)

        return output_doc

    def _read_input_doc_title(self):
        self._title_lang = None

        basename = os.path.basename(self._doc.file_path)
        basename_parts = basename.split('.')[:-1] # without the extension

        for part in basename_parts:
            if part in ALL_LANGS:
                self._title_lang = part
                logger.info(f'Detected target language in file name: {self._title_lang}')
                break

    def _read_input_doc_header(self):
        self._header_meta_lang = None

        for line in self._doc.lines:
            if isinstance(line, W3StringsCsvPlainComment):
                # if it's a random comment, ignore it
                pass
            elif isinstance(line, W3StringsCsvAttributeComment):
                match line.key:
                    case "meta[language":
                        meta_lang = line.value[:-1]
                        if meta_lang in ALL_LANGS_META_MAP.values():
                            self._header_meta_lang = meta_lang
                            logger.info('Detected language meta %s in file header', meta_lang)
                        else:
                            logger.error('Invalid header language meta: %s. Available values: %s', meta_lang, ALL_LANGS_META_MAP.values())
                    case _:
                        pass
            else:
                # if it's not a comment, the header section has finished
                break

    def _generate_output_header(self, output: W3StringsCsvDocument):
        meta_lang: str | None = None
        if self._header_meta_lang is not None:
            meta_lang = self._header_meta_lang
            logger.info("Encoding for language meta '%s' based on file header", meta_lang)
        elif self._title_lang is not None:
            meta_lang = ALL_LANGS_META_MAP.get(self._title_lang)
            logger.info("Encoding for language meta '%s' based on file name", meta_lang)
        else:
            meta_lang = 'en'
            logger.info('No language meta could be deduced. Defaulting to "en"')

        output.append(W3StringsCsvPlainComment(f'meta[language={meta_lang}]'))
        output.append(W3StringsCsvPlainComment('       id|key(hex)|key(str)|text'))

    def _generate_output_content(self, output: W3StringsCsvDocument):
        current_string_id_iter: StringIdSpaceIterator | None = None
        used_string_ids: set[StringId] = set()
        used_string_keys: set[str] = set()

        modded_detected_count = 0
        vanilla_detected_count = 0
        errored_detected_count = 0
        invalid_detected_count = 0

        for (line_idx, line) in enumerate(self._doc.lines):
            try:
                if isinstance(line, W3StringsCsvAttributeComment):
                    if line.key == _MOD_ID_COMMENT_KEY:
                        current_string_id_iter = None

                        mod_id = 0
                        try:
                            mod_id = int(line.value)
                        except ValueError:
                            logger.error('Failed to parse mod id value into a number: %s (line %d)', line.value, line_idx + 1)
                            continue

                        if mod_id < 0:
                            logger.error("Negative mod IDs are not permitted! (line %d)", line_idx + 1)
                            continue
                        if mod_id >= 100000:
                            logger.warning('Using mod ID with more than 5 digits: %d (line %d)', mod_id, line_idx + 1)

                        id_space = StringIdSpace.modern_modded(mod_id)
                        if id_space.start in used_string_ids:
                            logger.error("ID space for mod with ID %d established more than once (line %d)", mod_id, line_idx + 1)
                            continue

                        current_string_id_iter = iter(id_space)
                    elif line.key == _MOD_ID_LEGACY_COMMENT_KEY:
                        current_string_id_iter = None

                        mod_id = 0
                        try:
                            mod_id = int(line.value)
                        except ValueError:
                            logger.error('Failed to parse mod id value into a number: %s (line %d)', line.value, line_idx + 1)
                            continue

                        if mod_id < 0:
                            logger.error("Negative mod IDs are not permitted! (line %d)", line_idx + 1)
                            continue
                        if mod_id >= 10000:
                            logger.error('Using a mod ID greater than 9999 requires switching to a modern ID space convention (line %d)', mod_id, line_idx + 1)
                            continue

                        id_space = StringIdSpace.legacy_modded(mod_id)
                        if id_space.start in used_string_ids:
                            logger.error("ID space for mod with ID %d established more than once (line %d)", mod_id, line_idx + 1)
                            continue

                        current_string_id_iter = iter(id_space)

                elif isinstance(line, W3StringsCsvCompleteEntry):
                    if line.id in used_string_ids:
                        logger.error("String ID %d has already been used before (line %d)", line.id.id_num, line_idx + 1)
                        errored_detected_count += 1
                        continue
                    if line.key_str in used_string_keys:
                        logger.error("String key %s has already been used before (line %d)", line.key_str, line_idx + 1)
                        errored_detected_count += 1
                        continue

                    if line.id.is_vanilla():
                        output.append(line)
                        vanilla_detected_count += 1
                        used_string_ids.add(line.id)
                        if line.key_str != '':
                            used_string_keys.add(line.key_str)
                    elif line.id.is_modded():
                        output.append(line)
                        modded_detected_count += 1
                        used_string_ids.add(line.id)
                        if line.key_str != '':
                            used_string_keys.add(line.key_str)

                        # update currently used ID space for completing short entries
                        mod_id = line.id.mod_id()
                        id_space = line.id.id_space()
                        if line.id + 1 < id_space.stop:
                            current_string_id_iter = iter(id_space)
                            current_string_id_iter.advance_to(line.id + 1)
                    else:
                        logger.error("Found invalid string ID (line %d)", line_idx + 1)
                        invalid_detected_count += 1

                elif isinstance(line, W3StringsCsvShortEntry):
                    if line.key_str == '':
                        logger.error("String key must not be empty for a short entry (line %d)", line_idx + 1)
                        errored_detected_count += 1
                        continue
                    if line.key_str in used_string_keys:
                        logger.error("String key %s has already been used before (line %d)", line.key_str, line_idx + 1)
                        errored_detected_count += 1
                        continue
                    if current_string_id_iter is None:
                        logger.error("Valid ID space could not be attributed to line %d", line_idx + 1)
                        errored_detected_count += 1
                        continue
                    
                    id = StringId(0)
                    try:
                        id = current_string_id_iter.__next__()
                    except StopIteration:
                        logger.error("ID pool for the ID space %d has been exhausted (line %d)", current_string_id_iter.id_space.start, line_idx + 1)
                        if current_string_id_iter.id_space.is_legacy_modded():
                            logger.error("Consider switching to a modern REDkit convention, which gives access to 10 times as many IDs")
                        else:
                            logger.error("Consider using mutliple ID spaces for your mod. Add a ;mod_id=????? comment above this to signal ID space switch")

                        errored_detected_count += 1
                        current_string_id_iter = None
                        continue

                    complete = line.into_complete(id)
                    output.append(complete)
                    modded_detected_count += 1
                    used_string_ids.add(id)
                    used_string_keys.add(line.key_str)

            except Exception as ex:
                logger.error("Unexpected error at line %d: %s", line_idx + 1, ex)

        if modded_detected_count + vanilla_detected_count == 0:
            logger.warning("No valid string entries have been detected")
        if invalid_detected_count > 0:
            logger.error(
                "Detected invalid string IDs that are neigther vanilla nor correct modded string IDs. " \
                "Currently established string ID space convention can be found explained on the official Witcher 3 discord server: " \
                "https://discord.com/channels/597170291021709327/1326868944572907620/1326868944572907620"
            )

        logger.info("Completed generating CSV entries (%d mod entries, %d vanilla entries, %d entries with errors)",
                    modded_detected_count, vanilla_detected_count, errored_detected_count + invalid_detected_count)

        if errored_detected_count + invalid_detected_count > 0:
            raise Exception("Generating CSV entries finished with errors")
