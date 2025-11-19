from dataclasses import dataclass
import os
import traceback

import flet as ft

import flet_reactive as ftr
from w3stringsx_lib.localization import ALL_LANGS, ALL_LANGS_NAME_MAP
from w3stringsx_lib.logging import get_logger
from w3stringsx_lib.strings_db import StringsDb
from w3stringsx_svc import Configuration, StringsDbManagerService
from w3stringsx_gui.views.view_base import ViewBase
from w3stringsx_gui.routing import Routes
from w3stringsx_gui.components import StatusPill


@dataclass
class StringsDbEncodingViewProps:
    db_path: str | None = None

class StringsDbEncodingView(ViewBase):
    TITLE = "STRINGS DB ENCODING"
    PROPS_TYPE = StringsDbEncodingViewProps
    ALLOWED_EXTS = ['db']

    def __init__(self,
        config: Configuration,
        db_manager: StringsDbManagerService,
        props: StringsDbEncodingViewProps = StringsDbEncodingViewProps(db_path=None)
    ):
        self.__db_manager = db_manager

        self.__db_file_path: ftr.State[str | None] = self.use_state(None)
        self.__db_file_picker = ft.FilePicker(on_result=self.on_db_file_picked)
        self.__fallback_lang: ftr.State[str | None] = self.use_state(config.default_fallback_language.get_or_default())
        self.__lang_selection: dict[str, ftr.State[bool | None]] = { lang: self.use_state(True) for lang in ALL_LANGS }
        self.__output_dir_path: ftr.State[str | None] = self.use_state(None)
        self.__output_dir_picker = ft.FilePicker(on_result=self.on_output_dir_picked)

        self.__db_file_path.value = props.db_path

        self.__encoding_in_progress: ftr.State[bool | None] = self.use_state(False)
        self.__encoding_progress_text: ftr.State[str | None] = self.use_state(None)
        self.__encode_status_pill = StatusPill()

        super().__init__(
            route=Routes.ENCODE_DB,
            scroll=ft.ScrollMode.AUTO,
            spacing=30,
            controls=[
                # flet doesn't have database icons 😒
                ft.Row(
                    controls=[
                        ft.Image(
                            src="icons/database.svg",
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            width=32,
                            height=32
                        ),
                        ftr.ReactiveTextField(
                            value=self.__db_file_path,
                            label="Click to choose database file",
                            read_only=True,
                            expand=True,
                            border_color=ft.Colors.PRIMARY,
                            on_click=self.on_db_file_textfield_click,
                        ),
                    ]
                ),
                ft.Row(
                    spacing=15,
                    controls=[
                        ft.Icon(
                            name=ft.Icons.TRANSLATE,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ftr.ReactiveDropdown(
                            label="Fallback language",
                            value=self.__fallback_lang,
                            border_color=ft.Colors.PRIMARY,
                            menu_width=300,
                            menu_height=400,
                            options=[
                                ft.DropdownOption(
                                    key=lang,
                                    text=lang_name
                                ) for lang, lang_name in ALL_LANGS_NAME_MAP.items()
                            ]
                        ),
                    ]
                ),
                ftr.ReactiveContainer(
                    border=ft.border.all(1, ft.Colors.PRIMARY),
                    border_radius=5,
                    padding=ft.padding.only(left=10, top=5, right=10, bottom=10),
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                value="Select target languages"
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
                ftr.ReactiveTextField(
                    icon=ft.Icons.FOLDER,
                    value=self.__output_dir_path,
                    label="Click to choose output directory",
                    read_only=True,
                    border_color=ft.Colors.PRIMARY,
                    on_click=self.on_output_dir_textfield_click,
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
                                [self.__db_file_path, *self.__lang_selection.values(), self.__output_dir_path],
                                lambda: not bool(self.__db_file_path.value)
                                        or not any([selection.value is True for selection in self.__lang_selection.values()])
                                        or not bool(self.__output_dir_path.value)
                            )
                        )
                    ],
                ),
                ftr.ReactiveRow(
                    visible=self.__encoding_in_progress,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.ProgressRing(),
                        ftr.ReactiveText(value=self.__encoding_progress_text)
                    ]
                ),
                self.__encode_status_pill
            ]
        )

    def did_mount(self):
        super().did_mount()
        if (self.page):
            self.page.overlay.append(self.__db_file_picker)
            self.page.overlay.append(self.__output_dir_picker)

            self.__init_output_dir_to_first_input_dirname()

            self.page.update()

    def will_unmount(self):
        super().will_unmount()
        if (self.page):
            self.page.overlay.remove(self.__db_file_picker)
            self.page.overlay.remove(self.__output_dir_picker)

    
    def on_db_file_textfield_click(self, ev: ft.ControlEvent):
        db_dir: str | None = None
        if self.__db_file_path.value is not None:
            db_dir = os.path.dirname(self.__db_file_path.value)
        self.__db_file_picker.pick_files(
            file_type=ft.FilePickerFileType.CUSTOM,
            initial_directory=db_dir, # if None will use the default directory
            allow_multiple=False,
            allowed_extensions=self.ALLOWED_EXTS
        )

    def on_db_file_picked(self, ev: ft.FilePickerResultEvent):
        if ev.files is not None and len(ev.files) > 0:
            db_path = ev.files[0].path
            self.__db_file_path.value = db_path

            # set default output path when picking the first file(s)
            if not bool(self.__output_dir_path.value):
                self.__init_output_dir_to_first_input_dirname()


    def on_select_all_langs_button_click(self, ev: ft.ControlEvent):
        for _, selection in self.__lang_selection.items():
            selection.value = True

    def on_deselect_all_langs_button_click(self, ev: ft.ControlEvent):
        for _, selection in self.__lang_selection.items():
            selection.value = False


    def on_output_dir_textfield_click(self, ev: ft.ControlEvent):
        self.__output_dir_picker.get_directory_path(
            initial_directory=self.__output_dir_path.value # if empty will use the default value
        )

    def on_output_dir_picked(self, ev: ft.FilePickerResultEvent):
        if ev.path is not None:
            self.__output_dir_path.value = ev.path


    def on_encode_button_click(self, ev: ft.ControlEvent):
        logger = get_logger()

        if not bool(self.__db_file_path.value):
            logger.error("Database file not supplied. Aborting encode operation.")
            return
        if not bool(self.__fallback_lang.value):
            logger.error("Fallback language not supplied. Export aborted.")
            return
        if not any([selection.value is True for selection in self.__lang_selection.values()]):
            logger.error("No target languages selected. Aborting encode operation.")
            return
        if not bool(self.__output_dir_path.value):
            logger.error("Output directory not supplied. Aborting encode operation.")
            return
        
        errored = False
        self.__encoding_in_progress.value = True
        with StringsDb(self.__db_file_path.value) as db:
            try:
                selected_langs = [lang for lang, selection in self.__lang_selection.items() if selection.value]
                for i, lang in enumerate(selected_langs):
                    self.__encoding_progress_text.value = f"Encoding in progress... ({i+1}/{len(selected_langs)})"
                    self.__db_manager.encode_single_lang_w3strings(db, lang, self.__fallback_lang.value, self.__output_dir_path.value)
            except Exception as ex:
                logger.error(ex)
                logger.debug(traceback.format_exc())
                errored = True
        self.__encoding_in_progress.value = False
        self.__encoding_progress_text.value = None

        if not errored:
            self.__encode_status_pill.show("Database encoded successfully!")
        else:
            self.__encode_status_pill.show("Errors occured during encoding! Check the logs.", True)


    def __init_output_dir_to_first_input_dirname(self):
        # set default output path when picking the first file
        if self.__db_file_path.value:
            self.__output_dir_path.value = os.path.dirname(self.__db_file_path.value)
