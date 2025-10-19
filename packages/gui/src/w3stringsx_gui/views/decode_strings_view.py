from dataclasses import dataclass
import os
import traceback

import flet as ft

from w3stringsx_lib.logging import get_logger
from w3stringsx_ioc import di, Injected
from w3stringsx_svc import W3StringsManagerService
import flet_reactive as ftr
from w3stringsx_gui.routing import Router, Routes
from w3stringsx_gui.components import LogsPanel, StatusMessage


_logger = get_logger()


@dataclass
class DecodeStringsViewProps:
    w3strings_paths: list[str]

class DecodeStringsView(ft.View):
    TITLE = "DECODING"

    def __init__(self, 
        router: Router, props: object, 
        w3strings_manager: Injected[W3StringsManagerService] = di.inject(W3StringsManagerService)
    ):
        self.__w3strings_manager = w3strings_manager.resolve()

        self.__w3strings_file_paths = ftr.State[list[str]]([])
        self.__output_dir_path = ftr.State[str | None]('')
        self.__w3strings_file_picker = ft.FilePicker(on_result=self.on_w3strings_files_picked)
        self.__output_dir_picker = ft.FilePicker(on_result=self.on_output_dir_picked)
        self.__decode_status = ftr.State[bool | None](None)

        if not isinstance(props, DecodeStringsViewProps):
            props = DecodeStringsViewProps(w3strings_paths=[])
        
        self.__w3strings_file_paths.value.extend(props.w3strings_paths)
        VISIBLE_W3STRINGS_PATHS_ROWS = 5
        
        super().__init__(
            route=Routes.DECODE_STRINGS,
            controls=[
                ft.Column(
                    expand=True,
                    controls=[
                        ftr.ReactiveBuilder(
                            [self.__w3strings_file_paths],
                            lambda: ft.ListView(
                                auto_scroll=True,
                                height=300,
                                controls=[
                                    ft.DataTable(
                                        expand=True,
                                        heading_row_color=ft.Colors.PRIMARY_CONTAINER,
                                        # data_row_color=ft.Colors.SECONDARY_CONTAINER,
                                        vertical_lines=ft.border.BorderSide(1, ft.Colors.PRIMARY),
                                        horizontal_lines=ft.border.BorderSide(1, ft.Colors.PRIMARY),
                                        border=ft.border.all(1, ft.Colors.PRIMARY),
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
                                                            # color=ft.Colors.ON_SECONDARY_CONTAINER,
                                                        )),
                                                        ft.DataCell(ft.Text(
                                                            value=os.path.dirname(path),
                                                            # color=ft.Colors.ON_SECONDARY_CONTAINER,
                                                        )),
                                                    ]
                                                )
                                                for path in self.__w3strings_file_paths.value
                                            ]
                                            +
                                            # add placeholders so all rows are visible
                                            [
                                                ft.DataRow(
                                                    cells=[
                                                        ft.DataCell(ft.Text(), placeholder=True),
                                                        ft.DataCell(ft.Text(), placeholder=True),
                                                    ]
                                                ) for _ in range(VISIBLE_W3STRINGS_PATHS_ROWS - len(self.__w3strings_file_paths.value))
                                            ]
                                        ],
                                    ),
                                ],
                            ),
                        ),
                        ft.Row(
                            controls=[
                                ft.FilledButton(
                                    icon=ft.Icons.ATTACH_FILE,
                                    text="Add files...",
                                    on_click=self.on_pick_w3strings_file_button_click
                                ),
                                ft.FilledButton(
                                    icon=ft.Icons.CLEAR,
                                    text="Clear all",
                                    on_click=self.on_clear_w3strings_files_button_click
                                )
                            ]
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
                            # color=ft.Colors.ON_PRIMARY_CONTAINER,
                            border_color=ft.Colors.PRIMARY,
                            on_click=self.on_output_dir_textfield_click,
                        ),
                        ft.Row(
                            height=5
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ftr.ReactiveFilledButton(
                                    icon=ft.Icons.LOCK_OPEN,
                                    text='DECODE',
                                    width=300,
                                    on_click=self.on_decode_button_click,
                                    disabled=ftr.CompoundState(
                                        [self.__w3strings_file_paths, self.__output_dir_path],
                                        lambda: len(self.__w3strings_file_paths.value) == 0 
                                             or not self.__output_dir_path.value
                                    )        
                                )
                            ],
                        ),
                        StatusMessage(
                            self.__decode_status,
                            success_msg="Files decoded successfully!",
                            error_msg="Errors occured during decoding! Check the logs."
                        )
                    ],
                ),
                LogsPanel(
                    height=180
                ),
            ]
        )

    def did_mount(self):
        super().did_mount()
        if (self.page):
            self.page.overlay.append(self.__w3strings_file_picker)
            self.page.overlay.append(self.__output_dir_picker)
            self.page.update()

    def will_unmount(self):
        super().will_unmount()
        if (self.page):
            self.page.overlay.remove(self.__w3strings_file_picker)
            self.page.overlay.remove(self.__output_dir_picker)

    def on_pick_w3strings_file_button_click(self, ev: ft.ControlEvent):
        if len(self.__w3strings_file_paths.value) > 0:
            last_w3strings_file_path = self.__w3strings_file_paths.value[-1]
        else:
            last_w3strings_file_path = ''
        self.__w3strings_file_picker.pick_files(
            allow_multiple=True,
            allowed_extensions=['w3strings'],
            file_type=ft.FilePickerFileType.CUSTOM,
            initial_directory=os.path.dirname(last_w3strings_file_path)
        )

    def on_clear_w3strings_files_button_click(self, ev: ft.ControlEvent):
        self.__w3strings_file_paths.value = []

    def on_w3strings_files_picked(self, ev: ft.FilePickerResultEvent):
        if ev.files is not None:
            new_paths = self.__w3strings_file_paths.value.copy()
            for f in ev.files:
                # filter duplicates, but preserve order
                if f.path not in new_paths:
                    new_paths.append(f.path)
            self.__w3strings_file_paths.value = new_paths

            # set default output path when picking the first file
            if self.__output_dir_path.value == '' and len(new_paths) == 1:
                self.__output_dir_path.value = os.path.dirname(new_paths[0])

    def on_output_dir_textfield_click(self, ev: ft.ControlEvent):
        self.__output_dir_picker.get_directory_path(
            initial_directory=self.__output_dir_path.value
        )

    def on_output_dir_picked(self, ev: ft.FilePickerResultEvent):
        if ev.path is not None:
            self.__output_dir_path.value = ev.path

    def on_decode_button_click(self, ev: ft.ControlEvent):
        if self.__output_dir_path.value is None:
            return

        for input_path in self.__w3strings_file_paths.value:
            try:
                self.__w3strings_manager.decode_w3strings_to_csv(
                    input_path, 
                    self.__output_dir_path.value
                )
                self.__decode_status.value = True
            except Exception as ex:
                _logger.error(ex)
                _logger.debug(traceback.format_exc())
                self.__decode_status.value = False