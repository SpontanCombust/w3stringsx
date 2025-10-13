import os

import flet as ft

from w3stringsx_ioc import di, Injected
from w3stringsx_svc import W3StringsManagerService
from flet_reactive import Reactive, use_state
from w3stringsx_gui.routing import Router, Routes
from w3stringsx_gui.components import LogsPanel


class DecodeStringsViewProps:
    w3strings_paths: list[str] = []

class DecodeStringsView(ft.View):
    def __init__(self, 
        router: Router, props: object, 
        w3strings_manager: Injected[W3StringsManagerService] = di.inject(W3StringsManagerService)
    ):
        self.__w3strings_manager = w3strings_manager.resolve()
        self.__file_picker = ft.FilePicker(on_result=self.on_files_picked)
        self.__output_dir_picker = ft.FilePicker(on_result=self.on_output_directory_picked)
        self.__w3strings_paths = use_state(list[str]())
        self.__output_dir_path = use_state('')

        if not isinstance(props, DecodeStringsViewProps):
            props = DecodeStringsViewProps()
        
        self.__w3strings_paths.value.extend(props.w3strings_paths)
        VISIBLE_W3STRINGS_PATHS_ROWS = 5
        
        super().__init__(
            route=Routes.DECODE_STRINGS,
            controls=[
                ft.AppBar(title=ft.Text("DECODING")),
                ft.Column(
                    controls=[
                        Reactive(
                            [self.__w3strings_paths],
                            lambda: ft.ListView(
                                controls=[
                                    ft.DataTable(
                                        expand=True,
                                        heading_row_color=ft.Colors.PRIMARY_CONTAINER,
                                        data_row_color=ft.Colors.SECONDARY_CONTAINER,
                                        vertical_lines=ft.border.BorderSide(1, ft.Colors.SECONDARY),
                                        horizontal_lines=ft.border.BorderSide(1, ft.Colors.SECONDARY),
                                        border=ft.border.all(1, ft.Colors.SECONDARY),
                                        columns=[
                                            ft.DataColumn(ft.Text(
                                                value="File name",
                                                color=ft.Colors.ON_PRIMARY_CONTAINER,
                                            )),
                                            ft.DataColumn(ft.Text(
                                                value="File directory",
                                                color=ft.Colors.ON_PRIMARY_CONTAINER,
                                            )),
                                        ],
                                        rows=[
                                            *[
                                                ft.DataRow(
                                                    cells=[
                                                        ft.DataCell(ft.Text(
                                                            value=os.path.basename(path),
                                                            color=ft.Colors.ON_SECONDARY_CONTAINER,
                                                        )),
                                                        ft.DataCell(ft.Text(
                                                            value=os.path.dirname(path),
                                                            color=ft.Colors.ON_SECONDARY_CONTAINER,
                                                        )),
                                                    ]
                                                )
                                                for path in self.__w3strings_paths.value
                                            ]
                                            +
                                            # add placeholders so all rows are visible
                                            [
                                                ft.DataRow(
                                                    cells=[
                                                        ft.DataCell(ft.Text(), placeholder=True),
                                                        ft.DataCell(ft.Text(), placeholder=True),
                                                    ]
                                                ) for _ in range(VISIBLE_W3STRINGS_PATHS_ROWS - len(self.__w3strings_paths.value))
                                            ]
                                        ],
                                    ),
                                ],
                                auto_scroll=True,
                                height=300
                            ),
                        ),
                        ft.Row(
                            controls=[
                                ft.FilledButton(
                                    icon=ft.Icons.ATTACH_FILE,
                                    text="Add files...",
                                    on_click=self.on_pick_file_button_click
                                ),
                                ft.FilledButton(
                                    icon=ft.Icons.CLEAR,
                                    text="Clear all",
                                    on_click=self.on_clear_files_button_click
                                )
                            ]
                        ),
                        ft.Row(
                            height=10
                        ),
                        Reactive(
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
                                on_click=self.on_pick_output_dir_button_click,
                            ),
                        ),
                        Reactive(
                            [self.__w3strings_paths, self.__output_dir_path],
                            lambda: ft.Row(
                                controls=[
                                    ft.FilledButton(
                                        icon=ft.Icons.LOCK_OPEN,
                                        text='DECODE',
                                        width=300,
                                        on_click=self.on_decode_button_click,
                                        disabled=len(self.__w3strings_paths.value) == 0 
                                              or self.__output_dir_path.value == ''
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.CENTER
                            ),
                        ),
                    ],
                    expand=True
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
            self.page.overlay.append(self.__file_picker)
            self.page.overlay.append(self.__output_dir_picker)
            self.page.update()

    def will_unmount(self):
        super().will_unmount()
        if (self.page):
            self.page.overlay.remove(self.__file_picker)
            self.page.overlay.remove(self.__output_dir_picker)

    def on_pick_file_button_click(self, ev: ft.ControlEvent):
        self.__file_picker.pick_files(
            allow_multiple=True,
            allowed_extensions=['w3strings'],
            file_type=ft.FilePickerFileType.CUSTOM
        )

    def on_clear_files_button_click(self, ev: ft.ControlEvent):
        self.__w3strings_paths.value = []

    def on_files_picked(self, ev: ft.FilePickerResultEvent):
        if ev.files is not None:
            new_paths = self.__w3strings_paths.value.copy()
            for f in ev.files:
                # filter duplicates, but preserve order
                if f.path not in new_paths:
                    new_paths.append(f.path)
            self.__w3strings_paths.value = new_paths

            # set default output path when picking the first file
            if self.__output_dir_path.value == '' and len(new_paths) == 1:
                self.__output_dir_path.value = os.path.dirname(new_paths[0])

    def on_pick_output_dir_button_click(self, ev: ft.ControlEvent):
        self.__output_dir_picker.get_directory_path()

    def on_output_directory_picked(self, ev: ft.FilePickerResultEvent):
        if ev.path is not None:
            self.__output_dir_path.value = ev.path

    def on_decode_button_click(self, ev: ft.ControlEvent):
        for input_path in self.__w3strings_paths.value:
            self.__w3strings_manager.decode_w3strings_to_csv(input_path, self.__output_dir_path.value)