import asyncio
from dataclasses import dataclass
import os
import traceback
from typing import cast

import flet as ft

from w3stringsx_lib.logging import get_logger
from w3stringsx_lib.localization import ALL_LANGS
from w3stringsx_ioc import di, Injected
from w3stringsx_svc import W3StringsManagerService
from flet_reactive import ReactiveBuilder, State, use_state
from w3stringsx_gui.routing import Router, Routes
from w3stringsx_gui.components import LogsPanel, StatusMessage


_logger = get_logger()


@dataclass
class EncodeStringsViewProps:
    csv_path: str

class EncodeStringsView(ft.View):
    def __init__(self, 
        router: Router, props: object,
        w3strings_manager: Injected[W3StringsManagerService] = di.inject(W3StringsManagerService)
    ):
        self.__w3strings_manager = w3strings_manager.resolve()

        self.__csv_file_path = use_state('')
        self.__selected_langs = use_state(set(ALL_LANGS))
        self.__output_dir_path = use_state('')
        self.__keep_output_csv = use_state(False)
        self.__csv_file_picker = ft.FilePicker(on_result=self.on_csv_file_picked)
        self.__output_dir_picker = ft.FilePicker(on_result=self.on_output_dir_picked)
        self.__encode_status: State[bool | None] = use_state(None)

        if not isinstance(props, EncodeStringsViewProps):
            props = EncodeStringsViewProps(csv_path='')

        self.__csv_file_path.value = props.csv_path

        super().__init__(
            route=Routes.ENCODE_STRINGS,
            controls=[
                ft.AppBar(title=ft.Text("ENCODING")),
                ft.Column(
                    expand=True,
                    controls=[
                        ReactiveBuilder(
                            [self.__csv_file_path],
                            lambda: ft.TextField(
                                icon=ft.Icons.ATTACH_FILE,
                                value=self.__csv_file_path.value,
                                label="Click to choose the CSV file",
                                read_only=True,
                                expand=True,
                                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                                color=ft.Colors.PRIMARY,
                                border_color=ft.Colors.SECONDARY,
                                on_click=self.on_csv_file_path_textfield_click,
                            )
                        ),
                        ft.Row(
                            height=10
                        ),
                        ft.Container(
                            border=ft.border.all(1, ft.Colors.SECONDARY),
                            border_radius=5,
                            height=200,
                            padding=ft.padding.only(left=10, top=5, right=10, bottom=10),
                            content=ft.Column(
                                controls=[
                                    ft.Text(value="Select target languages:"),
                                    ReactiveBuilder(
                                        [self.__selected_langs],
                                        lambda: ft.GridView(
                                            expand=True,
                                            runs_count=9,
                                            child_aspect_ratio=2.5,
                                            spacing=10,
                                            run_spacing=10,
                                            controls=[
                                                ft.Checkbox(
                                                    label=ft.Text(value=lang, weight=ft.FontWeight.BOLD),
                                                    value=(lang in self.__selected_langs.value),
                                                    # adding lang=lang is IMPORTANT!!!
                                                    # otherwise it captures the variable by reference and then all calls are made for the last langugae only
                                                    on_change=lambda ev, lang=lang: self.on_selectable_lang_checkbox_change(ev, lang)
                                                ) for lang in ALL_LANGS
                                            ] 
                                        )
                                    ),
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
                        ReactiveBuilder(
                            [self.__output_dir_path],
                            lambda: ft.TextField(
                                icon=ft.Icons.FOLDER,
                                value=self.__output_dir_path.value,
                                label="Click to choose output directory",
                                read_only=True,
                                expand=True,
                                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                                color=ft.Colors.PRIMARY,
                                border_color=ft.Colors.SECONDARY,
                                on_click=self.on_output_dir_textfield_click,
                            ),
                        ),
                        ReactiveBuilder(
                            [self.__keep_output_csv],
                            lambda: ft.Checkbox(
                                label="Keep processed output CSV",
                                value=self.__keep_output_csv.value,
                                on_change=self.on_keep_output_csv_checkbox_change_change
                            ),
                        ),
                        ft.Row(
                            height=5
                        ),
                        ReactiveBuilder(
                            [self.__csv_file_path, self.__output_dir_path, self.__selected_langs],
                            lambda: ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.FilledButton(
                                        icon=ft.Icons.LOCK_OUTLINE,
                                        text='ENCODE',
                                        width=300,
                                        on_click=self.on_encode_button_click,
                                        disabled=self.__csv_file_path.value == ''
                                              or self.__output_dir_path.value == ''
                                              or len(self.__selected_langs.value) == 0
                                    )
                                ],
                            ),
                        ),
                        StatusMessage(
                            self.__encode_status,
                            success_msg="File encoded successfully!",
                            error_msg="Errors occured during encoding! Check the logs."
                        ),
                    ]
                ),
                LogsPanel(
                    height=180,
                    bgcolor=ft.Colors.SECONDARY_CONTAINER,
                    color=ft.Colors.ON_SECONDARY_CONTAINER
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
            allowed_extensions=['csv'],
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

    def on_selectable_lang_checkbox_change(self, ev: ft.ControlEvent, lang: str):
        checked = ev.data == 'true'
        if checked:
            new_set = self.__selected_langs.value.union([lang])
        else:
            new_set = self.__selected_langs.value.difference([lang])
        self.__selected_langs.value = new_set

    def on_select_all_langs_button_click(self, ev: ft.ControlEvent):
        self.__selected_langs.value = set(ALL_LANGS)

    def on_deselect_all_langs_button_click(self, ev: ft.ControlEvent):
        self.__selected_langs.value = set()

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
        try:
            self.__w3strings_manager.encode_w3strings_from_csv(
                self.__csv_file_path.value, 
                self.__output_dir_path.value,
                list(self.__selected_langs.value),
                self.__keep_output_csv.value
            )
            self.__encode_status.value = True
        except Exception as ex:
            _logger.error(ex)
            _logger.debug(ex)
            self.__encode_status.value = False
            