import dataclasses
import os
import traceback
from typing import cast

import flet as ft

from w3stringsx_lib.logging import get_logger
from w3stringsx_lib.localization import ALL_LANGS, ALL_LANGS_NAME_MAP
from w3stringsx_svc import W3StringsManagerService
import flet_reactive as ftr
from w3stringsx_gui.views.view_base import ViewBase
from w3stringsx_gui.routing import Routes
from w3stringsx_gui.components import StatusPill


_logger = get_logger()


@dataclasses.dataclass
class EncodeStringsViewProps:
    csv_paths: list[str] = dataclasses.field(default_factory=list)


class _CsvFileEntry:
    def __init__(self, csv_path: str, selected: ftr.State[bool | None], target_langs: list[str] = [], preferred_lang: str | None = None) -> None:
        self.csv_path = csv_path
        self.selected = selected
        self.target_langs = target_langs
        self.preferred_lang = preferred_lang

        if preferred_lang is None:
            basename = os.path.basename(csv_path)
            basename_parts = basename.split('.')[:-1] # without the extension
            for part in basename_parts:
                if part in ALL_LANGS:
                    self.preferred_lang = part
                    break

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, _CsvFileEntry):
            return False
        
        return self.csv_path == value.csv_path\
           and self.selected == value.selected\
           and self.target_langs == value.target_langs\
           and self.preferred_lang == value.preferred_lang
    
    def copy(self):
        return _CsvFileEntry(
            self.csv_path,
            self.selected,
            self.target_langs.copy(),
            self.preferred_lang
        )

class EncodeStringsView(ViewBase):
    TITLE = "ENCODING"
    PROPS_TYPE = EncodeStringsViewProps
    ALLOWED_EXTS = ['csv']

    def __init__(self, 
        w3strings_manager: W3StringsManagerService,
        props: EncodeStringsViewProps = EncodeStringsViewProps(csv_paths=[]),
    ):
        self.__w3strings_manager = w3strings_manager

        self.__csv_file_entries: ftr.ListState[_CsvFileEntry] = self.use_list_state([])
        self.__selected_csv_file_entry_idx: ftr.State[int | None] = self.use_state(None)
        # target languages assigned to currently selected CSV entry
        # True means that entry will be encoded to that language
        # False means it will not be
        # None means it cannot be encoded for that langauge, because other entry has already taken that language
        self.__lang_selection: dict[str, ftr.State[bool | None]] = { lang: self.use_state(None) for lang in ALL_LANGS }
        self.__output_dir_path: ftr.State[str | None] = self.use_state('')
        self.__keep_output_csv: ftr.State[bool | None] = self.use_state(False)
        self.__csv_file_picker = ft.FilePicker(on_result=self.on_csv_files_picked)
        self.__output_dir_picker = ft.FilePicker(on_result=self.on_output_dir_picked)
        self.__csv_file_entries.extend([_CsvFileEntry(path, self.use_state(False)) for path in props.csv_paths])
        VISIBLE_CSV_ENTRY_ROWS = 5

        self.__encode_status_pill = StatusPill()

        super().__init__(
            route=Routes.ENCODE_STRINGS,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ftr.ReactiveDataTable[_CsvFileEntry](
                    height=300,
                    heading_row_color=ft.Colors.PRIMARY_CONTAINER,
                    heading_text_style=ft.TextStyle(color=ft.Colors.ON_PRIMARY_CONTAINER),
                    vertical_lines=ft.border.BorderSide(1, ft.Colors.PRIMARY),
                    horizontal_lines=ft.border.BorderSide(1, ft.Colors.PRIMARY),
                    border=ft.border.all(1, ft.Colors.PRIMARY),
                    show_checkbox_column=False,
                    show_heading_checkbox=False,
                    columns=[
                        ftr.ReactiveDataColumn(
                            label=ft.Text("File name")
                        ),
                        ftr.ReactiveDataColumn(
                            label=ft.Text("File directory")
                        ),
                        ftr.ReactiveDataColumn(
                            label=ft.Text("Target languages")
                        ),
                    ],
                    rows_data=self.__csv_file_entries,
                    rows_mapper=lambda entry, idx: ftr.ReactiveDataRow(
                        cells=[
                            ft.DataCell(
                                content=ft.Text(
                                    value=os.path.basename(entry.csv_path)
                                )
                            ),
                            ft.DataCell(
                                content=ft.Text(
                                    value=os.path.dirname(entry.csv_path)
                                )
                            ),
                            ft.DataCell(
                                content=ft.Text(
                                    value=', '.join(entry.target_langs) if len(entry.target_langs) > 0
                                        else 'Please assign target languages',
                                    color=ft.Colors.ERROR if len(entry.target_langs) == 0 else None
                                )
                            ),
                        ],
                        selected=entry.selected,
                        on_select_changed=lambda ev, idx=idx: self.on_csv_file_entries_datarow_select_changed(ev, idx)
                    ),
                    placeholder_rows_count=VISIBLE_CSV_ENTRY_ROWS
                ),
                ft.Row(
                    controls=[
                        ft.FilledButton(
                            icon=ft.Icons.ATTACH_FILE,
                            text="Add files...",
                            on_click=self.on_pick_csv_files_button_click
                        ),
                        ft.FilledButton(
                            icon=ft.Icons.CLEAR,
                            text="Clear all",
                            on_click=self.on_clear_csv_files_button_click
                        )
                    ]
                ),
                ft.Row(
                    height=5
                ),
                ftr.ReactiveRow(
                    opacity=self.use_computed([self.__csv_file_entries], lambda:
                        1.0 if len(self.__csv_file_entries) > 0 else 0.0
                    ),
                    controls=[
                        ft.Icon(name=ft.Icons.INFO_OUTLINE),
                        ft.Text("Select an entry above to configure it")
                    ]
                ),
                ftr.ReactiveContainer(
                    border=ft.border.all(1, ft.Colors.PRIMARY),
                    border_radius=5,
                    padding=ft.padding.only(left=10, top=5, right=10, bottom=10),
                    disabled=self.use_computed([self.__selected_csv_file_entry_idx],
                        lambda: self.__selected_csv_file_entry_idx.value is None
                    ),
                    content=ft.Column(
                        controls=[
                            ftr.ReactiveText(
                                value=self.use_computed([self.__selected_csv_file_entry_idx, *self.__lang_selection.values()], self.lang_selection_label_text)
                            ),
                            ft.Row(
                                scroll=ft.ScrollMode.ALWAYS,
                                expand=True,
                                wrap=True,
                                spacing=0,
                                run_spacing=10,
                                controls=[
                                    ft.Container(
                                        width=250,
                                        content=ftr.ReactiveCheckbox(
                                            label=ft.Text(value=f'{lang_name} ({lang})', weight=ft.FontWeight.BOLD),
                                            value=self.__lang_selection[lang],
                                            disabled=self.use_computed([self.__lang_selection[lang]], 
                                                lambda lang=lang: self.__lang_selection[lang].value is None
                                            ),
                                            tristate=True,
                                            on_change=lambda ev, lang=lang: self.on_lang_selection_checkbox_changed(ev, lang),
                                        # display checkbox for each language, sorted by language name
                                        ) 
                                    ) for lang, lang_name in sorted(ALL_LANGS_NAME_MAP.items(), key=lambda kv: kv[1])
                                ]
                            ),
                            ft.Row(), # small spacer
                            ft.Row(
                                controls=[
                                    ft.FilledButton(
                                        icon=ft.Icons.CHECK,
                                        text="Select all",
                                        on_click=self.on_select_all_langs_button_click
                                    ),
                                    ft.FilledButton(
                                        icon=ft.Icons.CLEAR,
                                        text="Deselect all",
                                        on_click=self.on_deselect_all_langs_button_click
                                    ),
                                ]
                            )
                        ]
                    ) 
                ),
                ft.Row(
                    height=10
                ),
                ftr.ReactiveTextField(
                    icon=ft.Icons.FOLDER,
                    value=self.__output_dir_path,
                    label="Click to choose output directory",
                    read_only=True,
                    border_color=ft.Colors.PRIMARY,
                    on_click=self.on_output_dir_textfield_click,
                ),
                ftr.ReactiveCheckbox(
                    label="Keep generated end-result CSVs",
                    value=self.__keep_output_csv,
                ),
                ft.Row(
                    height=5
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ftr.ReactiveFilledButton(
                            icon=ft.Icons.LOCK_OUTLINE,
                            text='Encode',
                            width=300,
                            on_click=self.on_encode_button_click,
                            disabled=self.use_computed(
                                [self.__csv_file_entries, self.__output_dir_path],
                                lambda: len(self.__csv_file_entries) == 0
                                        or not all([len(entry.target_langs) > 0 for entry in self.__csv_file_entries]) # check if every CSV entry has any target language assigned to it
                                        or not self.__output_dir_path.value
                            )
                        )
                    ],
                ),
                self.__encode_status_pill,
            ]
        )

    def did_mount(self):
        super().did_mount()
        if (self.page):
            self.page.overlay.append(self.__csv_file_picker)
            self.page.overlay.append(self.__output_dir_picker)
            self.page.update()

    def will_unmount(self):
        super().will_unmount()
        if (self.page):
            self.page.overlay.remove(self.__csv_file_picker)
            self.page.overlay.remove(self.__output_dir_picker)


    def on_csv_file_entries_datarow_select_changed(self, ev: ft.ControlEvent, row_idx: int):
        if 0 <= row_idx < len(self.__csv_file_entries):
            changed_value = not self.__csv_file_entries[row_idx].selected.value
            # allow only a single row to be selected
            for entry in self.__csv_file_entries:
                entry.selected.value = False
            self.__csv_file_entries[row_idx].selected.value = changed_value
            self.__selected_csv_file_entry_idx.value = row_idx if changed_value is True else None
            self.__update_langugage_selections()

    def on_pick_csv_files_button_click(self, ev: ft.ControlEvent):
        self.__csv_file_picker.pick_files(
            allow_multiple=True,
            allowed_extensions=self.ALLOWED_EXTS,
            file_type=ft.FilePickerFileType.CUSTOM,
            initial_directory=os.path.dirname(self.__csv_file_entries[0].csv_path) if len(self.__csv_file_entries) > 0 else None
        )

    def on_csv_files_picked(self, ev: ft.FilePickerResultEvent):
        if ev.files is not None and len(ev.files) > 0:
            present_paths = [e.csv_path for e in self.__csv_file_entries]
            new_paths = [f.path for f in ev.files if f.path not in present_paths]

            if len(new_paths) > 0:
                new_entries = [_CsvFileEntry(path, self.use_state(False)) for path in new_paths]
                self.__csv_file_entries.extend(new_entries)

                self.__distribute_target_langs()

                # select the first row if none was selected beforehand
                if self.__selected_csv_file_entry_idx.value is None:
                    self.__selected_csv_file_entry_idx.value = 0
                    self.__csv_file_entries[0].selected.value = True

                self.__update_langugage_selections()

                # set default output path when picking the first file(s)
                if self.__output_dir_path.value == '':
                    self.__output_dir_path.value = os.path.dirname(new_paths[0])
    
    def on_clear_csv_files_button_click(self, ev: ft.ControlEvent):
        self.__csv_file_entries.clear()
        self.__selected_csv_file_entry_idx.value = None
        self.__update_langugage_selections()


    def lang_selection_label_text(self):
        selected = self.__get_selected_csv_file_entry()
        if selected:
            any_available_langs = any([selection.value is not None for selection in self.__lang_selection.values()])
            if any_available_langs:
                return f"Select target languages for {os.path.basename(selected.csv_path)}:"
            else:
                return "Deselect languages for other entries to be able to assign them for this entry"
        elif len(self.__csv_file_entries) > 0:
            return "Choose a file entry from list above to select target languages for it"
        else:
            return "Select target languages"

    # this should get called after state bound to the checkbox gets updated
    def on_lang_selection_checkbox_changed(self, ev: ft.ControlEvent, lang: str):
        # we want the checkbox to be able to display the third state,
        # but at the same time we do not want to allow the user to set it manually themselves
        # when that happens we quickly change None to False
        if self.__lang_selection[lang].value is None:
            self.__lang_selection[lang].value = False

        self.__update_selected_csv_file_entry_target_langs_from_selections()

    def on_select_all_langs_button_click(self, ev: ft.ControlEvent):
        for _, selection in self.__lang_selection.items():
            # enable only if its explicitly False
            # None is used as a disabling value
            if selection.value is not None:
                selection.value = True

        self.__update_selected_csv_file_entry_target_langs_from_selections()

    def on_deselect_all_langs_button_click(self, ev: ft.ControlEvent):
        for _, selection in self.__lang_selection.items():
            # same as above in select_all
            if selection.value is not None:
                selection.value = False

        self.__update_selected_csv_file_entry_target_langs_from_selections()


    def on_output_dir_textfield_click(self, ev: ft.ControlEvent):
        self.__output_dir_picker.get_directory_path(
            initial_directory=self.__output_dir_path.value # if empty will use the default value
        )

    def on_output_dir_picked(self, ev: ft.FilePickerResultEvent):
        if ev.path is not None:
            self.__output_dir_path.value = ev.path


    def on_encode_button_click(self, ev: ft.ControlEvent):
        if self.__output_dir_path.value is None:
            return

        errored = False
        for entry in self.__csv_file_entries:
            try:
                self.__w3strings_manager.encode_w3strings_from_csv(
                    entry.csv_path, 
                    self.__output_dir_path.value,
                    entry.target_langs,
                    self.__keep_output_csv.value or False
                )
            except Exception as ex:
                _logger.error(ex)
                _logger.debug(traceback.format_exc())
                errored = True

        if not errored:
            self.__encode_status_pill.show("File encoded successfully!")
        else:
            self.__encode_status_pill.show("Errors occured during encoding! Check the logs.", True)
                

    
    # User can supply multiple CSVs, which will correspond to different languages
    # target encoding languages however should not repeat between each CSV file
    # as this would inevitably lead to encoded files being uncontrollably overwritten.
    # For that the pool of available target languages needs to be distributed between CSVs.
    # User can decide which CSV gets assigned to given language at the end (if it's not taken by another CSV)
    # but we can deduce the initial configuration to shorten the process.
    def __distribute_target_langs(self):
        if len(self.__csv_file_entries) == 0:
            return
        
        changed_entries = [entry.copy() for entry in self.__csv_file_entries]

        lang_pool = set(ALL_LANGS)
        for entry in changed_entries:
            # first clear target langs for all entries 
            entry.target_langs = []
            # and assign only preferred language (deduced from file name)
            if entry.preferred_lang and entry.preferred_lang in lang_pool:
                entry.target_langs.append(entry.preferred_lang)
                lang_pool.remove(entry.preferred_lang)

        # now assign the rest of available languages
        # we assume that the user would want to encode for all possible languages
        if len(lang_pool) > 0:
            # the default fallback language should be English
            en_csvs = [entry for entry in changed_entries if entry.preferred_lang == 'en']
            if len(en_csvs) > 0:
                en_csvs[0].target_langs.extend(lang_pool)
            else:
                # if that couldn't be found, just any entry (the first one)
                changed_entries[0].target_langs.extend(lang_pool)

        # entries need to be reassigned to notify observers
        for i in range(len(self.__csv_file_entries)):
            changed_entries[i].target_langs.sort()
            self.__csv_file_entries[i] = changed_entries[i]

    def __get_selected_csv_file_entry(self) -> _CsvFileEntry | None:
        if self.__selected_csv_file_entry_idx.value is not None\
        and self.__selected_csv_file_entry_idx.value in range(0, len(self.__csv_file_entries)):
            return self.__csv_file_entries[self.__selected_csv_file_entry_idx.value]
        return None
    
    def __update_selected_csv_file_entry_target_langs_from_selections(self):
        if self.__selected_csv_file_entry_idx.value is not None\
        and self.__selected_csv_file_entry_idx.value in range(0, len(self.__csv_file_entries)):
            selected_entry = self.__csv_file_entries[self.__selected_csv_file_entry_idx.value]
            changed_entry = selected_entry.copy()
            changed_entry.target_langs = [lang for lang, selection in self.__lang_selection.items() if selection.value is True]
            self.__csv_file_entries[self.__selected_csv_file_entry_idx.value] = changed_entry

    def __update_langugage_selections(self):
        selected_entry = self.__get_selected_csv_file_entry()
        if selected_entry is None:
            for _, selection in self.__lang_selection.items():
                selection.value = None
        else:
            available_lang_pool = set(ALL_LANGS)
            for entry in self.__csv_file_entries:
                available_lang_pool.difference_update(entry.target_langs)

            for lang, selected in self.__lang_selection.items():
                if lang in available_lang_pool:
                    selected.value = False
                elif lang in selected_entry.target_langs:
                    selected.value = True
                else:
                    selected.value = None