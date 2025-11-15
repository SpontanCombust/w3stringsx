from dataclasses import dataclass
import os
import traceback

import flet as ft

import flet_reactive as ftr
from w3stringsx_lib.localization import ALL_LANGS, ALL_LANGS_NAME_MAP
from w3stringsx_lib.logging import get_logger
from w3stringsx_svc import Configuration
from w3stringsx_gui.views.view_base import ViewBase
from w3stringsx_gui.routing import Routes
from w3stringsx_gui.components import StatusPill


@dataclass
class StringsDbExportingViewProps:
    db_path: str | None = None

class StringsDbExportingView(ViewBase):
    TITLE = "STRINGS DB EXPORTING"
    PROPS_TYPE = StringsDbExportingViewProps
    ALLOWED_EXTS = ['db']

    def __init__(self,
        config: Configuration,
        props: StringsDbExportingViewProps = StringsDbExportingViewProps(db_path=None)
    ):
        self.__db_file_path: ftr.State[str | None] = self.use_state(None)
        self.__db_file_picker = ft.FilePicker(on_result=self.on_db_file_picked)
        self.__fallback_lang: ftr.State[str | None] = self.use_state(config.default_fallback_language.get_or_default())
        self.__single_file_export: ftr.State[bool | None] = self.use_state(False)
        self.__lang_selection: dict[str, ftr.State[bool | None]] = { lang: self.use_state(True) for lang in ALL_LANGS }
        self.__output_dir_path: ftr.State[str | None] = self.use_state(None)
        self.__output_dir_picker = ft.FilePicker(on_result=self.on_output_dir_picked)

        self.__db_file_path.value = props.db_path

        self.__can_export: ftr.Computed[bool | None] = self.use_computed(
            [self.__db_file_path, self.__single_file_export, *self.__lang_selection.values(), self.__output_dir_path],
            lambda: bool(self.__db_file_path.value)
                    and (self.__single_file_export.value is True 
                         or any([selection.value is True for selection in self.__lang_selection.values()]))
                    and bool(self.__output_dir_path.value)
        )
    
        self.__export_status_pill = StatusPill()

        super().__init__(
            route=Routes.ENCODE_DB,
            scroll=ft.ScrollMode.AUTO,
            spacing=30,
            controls=[
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
                ft.Column(
                    controls=[
                        ftr.ReactiveSwitch(
                            label="Export to a single file (REDkit format)",
                            value=self.__single_file_export
                        ),
                        ftr.ReactiveContainer(
                            border=ft.border.all(1, ft.Colors.PRIMARY),
                            border_radius=5,
                            padding=ft.padding.only(left=10, top=5, right=10, bottom=10),
                            disabled=self.__single_file_export,
                            content=ft.Column(
                                controls=[
                                    ft.Text(
                                        value="Select languages to export"
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
                    ]
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
                            width=300,
                            on_click=self.on_export_button_click,
                            disabled=self.use_computed([self.__can_export], lambda: not self.__can_export.value),
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ftr.ReactiveImage(
                                        src='icons/file-export-outline.svg',
                                        color=self.use_computed([self.__can_export], lambda:
                                            # this is close enough
                                            ft.Colors.ON_PRIMARY if self.__can_export.value else ft.Colors.with_opacity(0.4, ft.Colors.ON_SURFACE) 
                                        ),
                                        width=20,
                                        height=20,
                                    ),
                                    ft.Text(
                                        value="Export"
                                    )
                                ]
                            ),
                        ),
                    ]
                ),
                self.__export_status_pill
            ]
        )

    def did_mount(self):
        super().did_mount()
        if (self.page):
            self.page.overlay.append(self.__db_file_picker)
            self.page.overlay.append(self.__output_dir_picker)
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
            if self.__output_dir_path.value is None:
                self.__output_dir_path.value = os.path.dirname(db_path)


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


    def on_export_button_click(self, ev: ft.ControlEvent):
        if self.__db_file_path.value is None or self.__output_dir_path.value is None:
            return
        
        errored = False
        try:
            if self.__single_file_export.value:
                #TODO export to redkit CSV
                raise NotImplementedError()
            else:
                #TODO export to trad CSVs
                raise NotImplementedError()
        except Exception as ex:
            logger = get_logger()
            logger.error(ex)
            logger.debug(traceback.format_exc())
            errored = True
            
        if not errored:
            self.__export_status_pill.show("Database exported successfully!")
        else:
            self.__export_status_pill.show("Errors occured during export! Check the logs.", True)
