from dataclasses import dataclass
import os
import traceback

import flet as ft

from flet_reactive import ReactiveBuilder, use_state, State, Reactive
from w3stringsx_lib.logging import get_logger
from w3stringsx_ioc import Injected
from w3stringsx_svc import StringKeyDiscoveryService
from w3stringsx_gui.routing import Router, Routes
from w3stringsx_gui.components import StatusMessage, LogsPanel


_logger = get_logger()


@dataclass
class SearchForStringKeysViewProps:
    search_paths: list[str]
    
class SearchForStringKeysView(ft.View):
    TITLE = "STRING KEY SEARCH"

    def __init__(self, 
        router: Router, props: object,
        string_key_discovery = Injected(StringKeyDiscoveryService)
    ):
        self.__string_key_discovery = string_key_discovery.resolve()

        self.__search_paths = use_state(list[str]())
        self.__output_dir_path = use_state('')
        self.__search_regex = use_state('')
        self.__search_file_picker = ft.FilePicker(on_result=self.on_search_files_picked)
        self.__search_dir_picker = ft.FilePicker(on_result=self.on_search_dir_picked)
        self.__output_dir_picker = ft.FilePicker(on_result=self.on_output_dir_picked)
        self.__search_status: State[bool | None] = use_state(None)

        if not isinstance(props, SearchForStringKeysViewProps):
            props = SearchForStringKeysViewProps(search_paths=[])
        
        self.__search_paths.value.extend(props.search_paths)
        VISIBLE_SEARCH_PATHS_ROWS = 5

        super().__init__(
            route=Routes.SEARCH_FOR_STRING_KEYS,
            controls=[
                ft.Column(
                    expand=True,
                    controls=[
                        ReactiveBuilder(
                            [self.__search_paths],
                            lambda: ft.ListView(
                                auto_scroll=True,
                                height=300,
                                controls=[
                                    ft.DataTable(
                                        expand=True,
                                        heading_row_color=ft.Colors.PRIMARY_CONTAINER,
                                        vertical_lines=ft.border.BorderSide(1, ft.Colors.PRIMARY),
                                        horizontal_lines=ft.border.BorderSide(1, ft.Colors.PRIMARY),
                                        border=ft.border.all(1, ft.Colors.PRIMARY),
                                        columns=[
                                            ft.DataColumn(ft.Text(
                                                value="File or directory name",
                                                color=ft.Colors.ON_PRIMARY_CONTAINER,
                                            )),
                                            ft.DataColumn(ft.Text(
                                                value="Parent directory",
                                                color=ft.Colors.ON_PRIMARY_CONTAINER,
                                            )),
                                        ],
                                        rows=[
                                            *[
                                                ft.DataRow(
                                                    cells=[
                                                        ft.DataCell(ft.Text(
                                                            value=os.path.basename(path),
                                                        )),
                                                        ft.DataCell(ft.Text(
                                                            value=os.path.dirname(path),
                                                        )),
                                                    ]
                                                )
                                                for path in self.__search_paths.value
                                            ]
                                            +
                                            # add placeholders so all rows are visible
                                            [
                                                ft.DataRow(
                                                    cells=[
                                                        ft.DataCell(ft.Text(), placeholder=True),
                                                        ft.DataCell(ft.Text(), placeholder=True),
                                                    ]
                                                ) for _ in range(VISIBLE_SEARCH_PATHS_ROWS - len(self.__search_paths.value))
                                            ]
                                        ],
                                    ),
                                ],
                            ),
                        ),
                        ft.Text(value="Supported search targets: WitcherScript, user config XML, bundle XML, directory"),
                        ft.Row(
                            controls=[
                                ft.FilledButton(
                                    icon=ft.Icons.ATTACH_FILE,
                                    text="Add files...",
                                    on_click=self.on_pick_search_file_button_click
                                ),
                                ft.FilledButton(
                                    icon=ft.Icons.FOLDER,
                                    text="Add folder...",
                                    on_click=self.on_pick_search_dir_button_click
                                ),
                                ft.FilledButton(
                                    icon=ft.Icons.CLEAR,
                                    text="Clear all",
                                    on_click=self.on_clear_search_paths_button_click
                                )
                            ]
                        ),
                        ft.Row(
                            height=5
                        ),
                        ft.Container(
                            ft.TextField(
                                icon=ft.Icons.MANAGE_SEARCH,
                                value=self.__search_regex.value,
                                label="Common string key pattern",
                                hint_text='E.g. prefix "my_mod_". Supports regex.',
                                expand=True,
                                border_color=ft.Colors.PRIMARY,
                                on_change=self.on_search_regex_textfield_change,
                            ),
                        ),
                        ft.Row(
                            height=5
                        ),
                        ReactiveBuilder(
                            [self.__output_dir_path],
                            lambda: ft.TextField(
                                icon=ft.Icons.FOLDER,
                                value=self.__output_dir_path.value,
                                label="Click to choose output directory",
                                read_only=True,
                                expand=True,
                                border_color=ft.Colors.PRIMARY,
                                on_click=self.on_output_dir_textfield_click,
                            ),
                        ),
                        ft.Row(
                            height=5
                        ),
                        ReactiveBuilder(
                            [self.__search_paths, self.__search_regex, self.__output_dir_path],
                            lambda: ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.FilledButton(
                                        icon=ft.Icons.SEARCH,
                                        text='SEARCH',
                                        width=300,
                                        on_click=self.on_search_button_click,
                                        disabled=len(self.__search_paths.value) == 0
                                              or self.__search_regex.value == ''
                                              or self.__output_dir_path.value == ''
                                    )
                                ],
                            ),
                        ),
                        StatusMessage(
                            self.__search_status,
                            success_msg="Files and/or directories searched successfully!",
                            error_msg="Errors occured during the search! Check the logs."
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
            self.page.overlay.append(self.__search_file_picker)
            self.page.overlay.append(self.__search_dir_picker)
            self.page.overlay.append(self.__output_dir_picker)
            self.page.update()

    def will_unmount(self):
        super().will_unmount()
        if (self.page):
            self.page.overlay.remove(self.__search_file_picker)
            self.page.overlay.remove(self.__search_dir_picker)
            self.page.overlay.remove(self.__output_dir_picker)


    def on_pick_search_file_button_click(self, ev: ft.ControlEvent):
        self.__search_file_picker.pick_files(
            allow_multiple=True,
            allowed_extensions=['xml', 'ws', 'wss'],
            file_type=ft.FilePickerFileType.CUSTOM,
        )

    def on_search_files_picked(self, ev: ft.FilePickerResultEvent):
        if ev.files is not None:
            paths = self.__search_paths.value.copy()
            for f in ev.files:
                # filter duplicates, but preserve order
                if f.path not in paths:
                    paths.append(f.path)
            self.__search_paths.value = paths

            # set default output path when picking the first file
            if self.__output_dir_path.value == '' and len(paths) == 1:
                self.__output_dir_path.value = os.path.dirname(paths[0])

    def on_pick_search_dir_button_click(self, ev: ft.ControlEvent):
        self.__search_dir_picker.get_directory_path()

    def on_search_dir_picked(self, ev: ft.FilePickerResultEvent):
        if ev.path is not None and ev.path not in self.__search_paths.value:
            self.__search_paths.value = self.__search_paths.value + [ev.path]

            # set default output path when picking the first file
            if self.__output_dir_path.value == '':
                self.__output_dir_path.value = os.path.dirname(ev.path)

    def on_clear_search_paths_button_click(self, ev: ft.ControlEvent):
        self.__search_paths.value = []


    def on_search_regex_textfield_change(self, ev: ft.ControlEvent):
        self.__search_regex.value = str(ev.data)


    def on_output_dir_textfield_click(self, ev: ft.ControlEvent):
        self.__output_dir_picker.get_directory_path(
            initial_directory=self.__output_dir_path.value
        )

    def on_output_dir_picked(self, ev: ft.FilePickerResultEvent):
        if ev.path is not None:
            self.__output_dir_path.value = ev.path


    def on_search_button_click(self, ev: ft.ControlEvent):
        for input_path in self.__search_paths.value:
            try:
                if os.path.isdir(input_path):
                    self.__string_key_discovery.discover_str_keys_in_directory(input_path, self.__output_dir_path.value, self.__search_regex.value)
                elif input_path.endswith('.xml'):
                    self.__string_key_discovery.discover_str_keys_in_xml(input_path, self.__output_dir_path.value, self.__search_regex.value)
                elif input_path.endswith(('.ws', '.wss')):
                    self.__string_key_discovery.discover_str_keys_in_witcherscript(input_path, self.__output_dir_path.value, self.__search_regex.value)

                self.__search_status.value = True
            except Exception as ex:
                _logger.error(ex)
                _logger.debug(traceback.format_exc())
                self.__search_status.value = False