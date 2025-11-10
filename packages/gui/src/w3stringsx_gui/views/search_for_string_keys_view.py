import dataclasses
import os
import traceback

import flet as ft

import flet_reactive as ftr
from w3stringsx_lib.logging import get_logger
from w3stringsx_svc import StringKeyDiscoveryService
from w3stringsx_gui.routing import Routes
from w3stringsx_gui.components import StatusMessage, LogsPanel


_logger = get_logger()


@dataclasses.dataclass
class SearchForStringKeysViewProps:
    search_paths: list[str] = dataclasses.field(default_factory=list)
    
class SearchForStringKeysView(ft.View):
    TITLE = "STRING KEY SEARCH"
    PROPS_TYPE = SearchForStringKeysViewProps
    ALLOWED_EXTS = ['xml', 'ws', 'wss']

    def __init__(self, 
        string_key_discovery: StringKeyDiscoveryService,
        props: SearchForStringKeysViewProps = SearchForStringKeysViewProps(search_paths=[]),
    ):
        self.__string_key_discovery = string_key_discovery

        self.__search_paths = ftr.ListState[str]([])
        self.__output_dir_path = ftr.State[str | None]('')
        self.__search_regex = ftr.State[str | None]('')
        self.__search_file_picker = ft.FilePicker(on_result=self.on_search_files_picked)
        self.__search_dir_picker = ft.FilePicker(on_result=self.on_search_dir_picked)
        self.__output_dir_picker = ft.FilePicker(on_result=self.on_output_dir_picked)
        self.__search_status = ftr.State[bool | None](None)

        if not isinstance(props, SearchForStringKeysViewProps):
            props = SearchForStringKeysViewProps(search_paths=[])
        
        self.__search_paths.extend(props.search_paths)
        VISIBLE_SEARCH_PATHS_ROWS = 5

        super().__init__(
            route=Routes.SEARCH_FOR_STRING_KEYS,
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
                                    label=ft.Text(
                                        value="File or directory name"
                                    )
                                ),
                                ftr.ReactiveDataColumn(
                                    label=ft.Text(
                                        value="Parent directory",
                                    )
                                ),
                            ],
                            rows_data=self.__search_paths,
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
                            placeholder_rows_count=VISIBLE_SEARCH_PATHS_ROWS
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
                        ftr.ReactiveTextField(
                            icon=ft.Icons.MANAGE_SEARCH,
                            value=self.__search_regex,
                            label="Common string key pattern",
                            hint_text='E.g. prefix "my_mod_". Supports regex.',
                            border_color=ft.Colors.PRIMARY
                        ),
                        ft.Row(
                            height=5
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
                            height=5
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ftr.ReactiveFilledButton(
                                    icon=ft.Icons.SEARCH,
                                    text='SEARCH',
                                    width=300,
                                    on_click=self.on_search_button_click,
                                    disabled=ftr.CompoundState(
                                        [self.__search_paths, self.__search_regex, self.__output_dir_path],
                                        lambda: len(self.__search_paths) == 0
                                             or not self.__search_regex.value
                                             or not self.__output_dir_path.value
                                    )
                                )
                            ],
                        ),
                        StatusMessage(
                            self.__search_status,
                            success_msg="Files and/or directories searched successfully!",
                            error_msg="Errors occured during the search! Check the logs."
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
            allowed_extensions=self.ALLOWED_EXTS,
            file_type=ft.FilePickerFileType.CUSTOM,
        )

    def on_search_files_picked(self, ev: ft.FilePickerResultEvent):
        if ev.files is not None:
            for f in ev.files:
                # filter duplicates, but preserve order
                if f.path not in self.__search_paths:
                    self.__search_paths.append(f.path)

            # set default output path when picking the first file
            if self.__output_dir_path.value == '' and len(self.__search_paths) == 1:
                self.__output_dir_path.value = os.path.dirname(self.__search_paths[0])

    def on_pick_search_dir_button_click(self, ev: ft.ControlEvent):
        self.__search_dir_picker.get_directory_path()

    def on_search_dir_picked(self, ev: ft.FilePickerResultEvent):
        if ev.path is not None and ev.path not in self.__search_paths:
            self.__search_paths.append(ev.path)

            # set default output path when picking the first file
            if self.__output_dir_path.value == '':
                self.__output_dir_path.value = os.path.dirname(ev.path)

    def on_clear_search_paths_button_click(self, ev: ft.ControlEvent):
        self.__search_paths.clear()


    def on_output_dir_textfield_click(self, ev: ft.ControlEvent):
        self.__output_dir_picker.get_directory_path(
            initial_directory=self.__output_dir_path.value
        )

    def on_output_dir_picked(self, ev: ft.FilePickerResultEvent):
        if ev.path is not None:
            self.__output_dir_path.value = ev.path


    def on_search_button_click(self, ev: ft.ControlEvent):
        if self.__output_dir_path.value is None\
        or self.__search_regex.value is None:
            return
        
        for input_path in self.__search_paths:
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