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
from w3stringsx_gui.components import LogsPanel, StatusMessage


_logger = get_logger()


@dataclasses.dataclass
class EncodeStringsViewProps:
    csv_path: str | None = None

class EncodeStringsView(ViewBase):
    TITLE = "ENCODING"
    PROPS_TYPE = EncodeStringsViewProps
    ALLOWED_EXTS = ['csv']

    def __init__(self, 
        w3strings_manager: W3StringsManagerService,
        props: EncodeStringsViewProps = EncodeStringsViewProps(csv_path=''),
    ):
        self.__w3strings_manager = w3strings_manager

        self.__csv_file_path: ftr.State[str | None] = self.use_state('')
        self.__lang_selection: dict[str, ftr.State[bool | None]] = { lang: self.use_state(True) for lang in ALL_LANGS }
        self.__output_dir_path: ftr.State[str | None] = self.use_state('')
        self.__keep_output_csv: ftr.State[bool | None] = self.use_state(False)
        self.__csv_file_picker = ft.FilePicker(on_result=self.on_csv_file_picked)
        self.__output_dir_picker = ft.FilePicker(on_result=self.on_output_dir_picked)
        self.__encode_status: ftr.State[bool | None] = self.use_state(None)

        self.__csv_file_path.value = props.csv_path

        super().__init__(
            route=Routes.ENCODE_STRINGS,
            controls=[
                ft.Column(
                    expand=True,
                    controls=[
                        ftr.ReactiveTextField(
                            icon=ft.Icons.ATTACH_FILE,
                            value=self.__csv_file_path,
                            label="Click to choose the CSV file",
                            read_only=True,
                            # bgcolor=ft.Colors.PRIMARY_CONTAINER,
                            # color=ft.Colors.PRIMARY,
                            border_color=ft.Colors.PRIMARY,
                            on_click=self.on_csv_file_path_textfield_click,
                        ),
                        ft.Row(
                            height=10
                        ),
                        ft.Container(
                            border=ft.border.all(1, ft.Colors.PRIMARY),
                            border_radius=5,
                            height=200,
                            padding=ft.padding.only(left=10, top=5, right=10, bottom=10),
                            content=ft.Column(
                                scroll=ft.ScrollMode.ADAPTIVE,
                                controls=[
                                    ft.Text(value="Select target languages:"),
                                    ft.GridView(
                                        expand=True,
                                        runs_count=6,
                                        run_spacing=100,
                                        child_aspect_ratio=5.5,
                                        controls=[
                                            ftr.ReactiveCheckbox(
                                                label=ft.Text(value=f'{ALL_LANGS_NAME_MAP[lang]} ({lang})', weight=ft.FontWeight.BOLD),
                                                value=self.__lang_selection[lang]
                                            ) for lang in ALL_LANGS
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
                            # bgcolor=ft.Colors.PRIMARY_CONTAINER,
                            # color=ft.Colors.PRIMARY,
                            border_color=ft.Colors.PRIMARY,
                            on_click=self.on_output_dir_textfield_click,
                        ),
                        ftr.ReactiveCheckbox(
                            label="Keep generated end-result CSV",
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
                                        [self.__csv_file_path, self.__output_dir_path, *self.__lang_selection.values()],
                                        lambda: not self.__csv_file_path.value
                                             or not self.__output_dir_path.value
                                             or all([not selection.value for selection in self.__lang_selection.values()])
                                    )
                                )
                            ],
                        ),
                        StatusMessage(
                            self.__encode_status,
                            success_msg="File encoded successfully!",
                            error_msg="Errors occured during encoding! Check the logs."
                        ),
                    ]
                ),
                LogsPanel(
                    height=300
                ),
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


    def on_csv_file_path_textfield_click(self, ev: ft.ControlEvent):
        self.__csv_file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=self.ALLOWED_EXTS,
            file_type=ft.FilePickerFileType.CUSTOM,
            initial_directory=os.path.dirname(self.__csv_file_path.value) if self.__csv_file_path.value else None
        )

    def on_csv_file_picked(self, ev: ft.FilePickerResultEvent):
        if ev.files is not None and len(ev.files) > 0:
            csv_path = ev.files[0].path
            self.__csv_file_path.value = csv_path

            # set default output path when picking the first file
            if self.__output_dir_path.value == '':
                self.__output_dir_path.value = os.path.dirname(csv_path)

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

    def on_keep_output_csv_checkbox_change_change(self, ev: ft.ControlEvent):
        self.__keep_output_csv.value = cast(ft.Checkbox, ev.control).value or False

    def on_encode_button_click(self, ev: ft.ControlEvent):
        if self.__csv_file_path.value is None\
            or self.__output_dir_path.value is None:
            return
        
        try:
            self.__w3strings_manager.encode_w3strings_from_csv(
                self.__csv_file_path.value, 
                self.__output_dir_path.value,
                [lang for lang, selection in self.__lang_selection.items() if selection.value == True],
                self.__keep_output_csv.value or False
            )
            self.__encode_status.value = True
        except Exception as ex:
            _logger.error(ex)
            _logger.debug(traceback.format_exc())
            self.__encode_status.value = False
            