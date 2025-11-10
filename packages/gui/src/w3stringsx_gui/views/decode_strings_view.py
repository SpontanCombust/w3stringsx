import dataclasses
import os
import traceback

import flet as ft

from w3stringsx_lib.logging import get_logger
from w3stringsx_svc import W3StringsManagerService
import flet_reactive as ftr
from w3stringsx_gui.views.view_base import ViewBase
from w3stringsx_gui.routing import Routes
from w3stringsx_gui.components import LogsPanel, StatusMessage


_logger = get_logger()


@dataclasses.dataclass
class DecodeStringsViewProps:
    w3strings_paths: list[str] = dataclasses.field(default_factory=list)

class DecodeStringsView(ViewBase, ftr.ReactiveHooks):
    TITLE = "DECODING"
    PROPS_TYPE = DecodeStringsViewProps
    ALLOWED_EXTS = ['w3strings']

    def __init__(self, 
        w3strings_manager: W3StringsManagerService,
        props: DecodeStringsViewProps = DecodeStringsViewProps(w3strings_paths=[])
    ):
        self.__w3strings_manager = w3strings_manager

        self.__w3strings_file_paths: ftr.ListState[str] = self.use_list_state([])
        self.__output_dir_path: ftr.State[str | None] = self.use_state('')
        self.__w3strings_file_picker = ft.FilePicker(on_result=self.on_w3strings_files_picked)
        self.__output_dir_picker = ft.FilePicker(on_result=self.on_output_dir_picked)
        self.__decode_status: ftr.State[bool | None] = self.use_state(None)

        self.__w3strings_file_paths.extend(props.w3strings_paths)
        VISIBLE_W3STRINGS_PATHS_ROWS = 5
        
        super().__init__(
            route=Routes.DECODE_STRINGS,
            controls=[
                ft.Column(
                    expand=True,
                    controls=[
                        ftr.ReactiveDataTable(
                            height=300,
                            heading_row_color=ft.Colors.PRIMARY_CONTAINER,
                            heading_text_style=ft.TextStyle(color=ft.Colors.ON_PRIMARY_CONTAINER),
                            vertical_lines=ft.border.BorderSide(1, ft.Colors.PRIMARY),
                            horizontal_lines=ft.border.BorderSide(1, ft.Colors.PRIMARY),
                            border=ft.border.all(1, ft.Colors.PRIMARY),
                            columns=[
                                ftr.ReactiveDataColumn(
                                    label=ft.Text("File name")
                                ),
                                ftr.ReactiveDataColumn(
                                    label=ft.Text("File directory")
                                ),
                            ],
                            rows_data=self.__w3strings_file_paths,
                            rows_mapper=lambda path: ftr.ReactiveDataRow(
                                cells=[
                                    ft.DataCell(
                                        content=ft.Text(
                                            value=os.path.basename(path)
                                        )
                                    ),
                                    ft.DataCell(
                                        content=ft.Text(
                                            value=os.path.dirname(path)
                                        )
                                    ),
                                ]
                            ),
                            placeholder_rows_count=VISIBLE_W3STRINGS_PATHS_ROWS
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
                                    disabled=self.use_computed(
                                        [self.__w3strings_file_paths, self.__output_dir_path],
                                        lambda: len(self.__w3strings_file_paths) == 0 
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
                    height=300
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
        if len(self.__w3strings_file_paths) > 0:
            last_w3strings_file_path = self.__w3strings_file_paths[-1]
        else:
            last_w3strings_file_path = ''
        self.__w3strings_file_picker.pick_files(
            allow_multiple=True,
            allowed_extensions=self.ALLOWED_EXTS,
            file_type=ft.FilePickerFileType.CUSTOM,
            initial_directory=os.path.dirname(last_w3strings_file_path)
        )

    def on_clear_w3strings_files_button_click(self, ev: ft.ControlEvent):
        self.__w3strings_file_paths.clear()

    def on_w3strings_files_picked(self, ev: ft.FilePickerResultEvent):
        if ev.files is not None:
            for f in ev.files:
                # filter duplicates, but preserve order
                if f.path not in self.__w3strings_file_paths:
                    self.__w3strings_file_paths.append(f.path)

            # set default output path when picking the first file
            if self.__output_dir_path.value == '' and len(self.__w3strings_file_paths) == 1:
                self.__output_dir_path.value = os.path.dirname(self.__w3strings_file_paths[0])

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

        for input_path in self.__w3strings_file_paths:
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