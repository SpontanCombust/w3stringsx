import os

from w3stringsx_lib.logging import get_logger
from w3stringsx_lib.strings_db import StringsDb
from w3stringsx_lib.w3strings_csv import W3StringsCsvDocument, W3StringsCsvCompleteEntry, StringId
from w3stringsx_lib.w3strings_csv_encoding_preprocessor import W3StringsCsvDocumentEncodingPreprocessor
from w3stringsx_lib.localization import ALL_LANGS_NAME_MAP
from w3stringsx_lib.strings_db.export_csv import StringsDbExportCsvDocument, StringsDbExportCsvLine
from w3stringsx_lib.utils import replace_path_dirname
from w3stringsx_svc.validators import validate_output_dir, validate_lang


logger = get_logger()

class StringsDbManagerService:
    def __init__(self) -> None:
        pass


    def export_single_lang_csv(self, db: StringsDb, lang: str, fallback_lang: str, output_dir: str):
        lang = validate_lang(lang)
        fallback_lang = validate_lang(fallback_lang)
        output_dir = validate_output_dir(output_dir)

        doc_path = os.path.join(output_dir, f'{lang}.csv')
        doc = W3StringsCsvDocument(doc_path)

        lang_repo = db.languages_repository()
        lang_model = lang_repo.select_by_name(lang.upper())
        if lang_model is None:
            raise Exception('Language not found in database')
        fallback_lang_model = lang_repo.select_by_name(fallback_lang.upper())
        if fallback_lang_model is None:
            raise Exception('Fallback language not found in database')
        
        strings_repo = db.strings_repository()
        rows = strings_repo.select_latest_with_info_short(langs=[lang_model.id, fallback_lang_model.id], order_by_string_id=True)
        last_strings_id = -1
        for r in rows:
            if r.string_id == last_strings_id:
                # a situation where the previous row was for the fallback language and now we got the target language, 
                # so we need to replace that fallback row with proper row
                # thanks to ordering by string id we have a guarantee they would be placed next to each other
                if r.lang == lang_model.id:
                    doc.pop()
                # a situation where the previous row was the target language and currently we're processing the fallback
                # this time we ignore the row altogether
                else:
                    continue

            entry = W3StringsCsvCompleteEntry(
                id=StringId(r.string_id),
                key_hex='',
                key_str=r.string_key or '',
                text=r.text or '' 
            )
            doc.append(entry)

            last_strings_id = r.string_id

        doc_proc = W3StringsCsvDocumentEncodingPreprocessor(doc)
        doc = doc_proc.process_to(doc_path)

        doc.save_to_file()

        logger.info('%s database strings have been successfully exported to %s', ALL_LANGS_NAME_MAP[lang], doc_path)


    def export_redkit_csv(self, db: StringsDb, output_dir: str):
        output_dir = validate_output_dir(output_dir)

        if db.db_path is None:
            raise Exception('Database not opened from file')

        db_path_root, _ = os.path.splitext(db.db_path)
        doc_path = replace_path_dirname(f'{db_path_root}_export.csv', output_dir)
        doc = StringsDbExportCsvDocument(doc_path)
        
        lang_repo = db.languages_repository()
        lang_models = lang_repo.select_all()
        lang_model_lower_name_map: dict[int, str] = { model.id: model.lang.lower() for model in lang_models }

        strings_repo = db.strings_repository()
        rows = strings_repo.select_latest_with_info(order_by_string_id=True)
        last_strings_id = -1
        for r in rows:
            if r.string_id == last_strings_id:
                line = doc.lines[-1]
            else:
                line = StringsDbExportCsvLine(
                    id=r.string_id,
                    resource=r.resource,
                    property=r.property_name,
                    voiceover=r.voiceover_name,
                    key=r.string_key
                )
                doc.append(line)
                
            if r.lang is not None:
                line_lang_prop = lang_model_lower_name_map[r.lang]
                setattr(line, line_lang_prop, r.text)
            
            last_strings_id = r.string_id

        doc.save_to_file()

        logger.info('Database strings have been successfully exported to %s', doc_path)