import dataclasses
import os
import traceback

import flet as ft

import flet_reactive as ftr
from w3stringsx_lib.logging import get_logger
from w3stringsx_svc import StringKeyDiscoveryService
from w3stringsx_gui.views.view_base import ViewBase
from w3stringsx_gui.routing import Routes
from w3stringsx_gui.components import StatusPill


@dataclasses.dataclass
class SearchForStringKeysViewProps:
    search_paths: list[str] = dataclasses.field(default_factory=list)
    
class SearchForStringKeysView(ViewBase):
    TITLE = "STRING KEY SEARCH"
    PROPS_TYPE = SearchForStringKeysViewProps
    ALLOWED_EXTS = ['xml', 'ws', 'wss']

    def __init__(self, 
        string_key_discovery: StringKeyDiscoveryService,
        props: SearchForStringKeysViewProps = SearchForStringKeysViewProps(search_paths=[]),
    ):
        self.__string_key_discovery = string_key_discovery

        self.__search_paths: ftr.ListState[str] = self.use_list_state([])
        self.__output_dir_path: ftr.State[str | None] = self.use_state('')
        self.__search_regex: ftr.State[str | None] = self.use_state('')
        self.__search_file_picker = ft.FilePicker(on_result=self.on_search_files_picked)
        self.__search_dir_picker = ft.FilePicker(on_result=self.on_search_dir_picked)
        self.__output_dir_picker = ft.FilePicker(on_result=self.on_output_dir_picked)

        self.__search_in_progress: ftr.State[bool | None] = self.use_state(False)
        self.__search_paths.extend(props.search_paths)
        VISIBLE_SEARCH_PATHS_ROWS = 5

        self.__search_status_pill = StatusPill()

        super().__init__(
            route=Routes.SEARCH_FOR_STRING_KEYS,
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
                    rows_mapper=lambda path, _: ftr.ReactiveDataRow(
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
                            text='Search',
                            width=300,
                            on_click=self.on_search_button_click,
                            disabled=self.use_computed(
                                [self.__search_paths, self.__search_regex, self.__output_dir_path],
                                lambda: not bool(self.__search_paths)
                                        or not bool(self.__search_regex.value)
                                        or not bool(self.__output_dir_path.value)
                            )
                        )
                    ],
                ),
                ftr.ReactiveRow(
                    visible=self.__search_in_progress,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.ProgressRing(),
                        ft.Text(value="Searching...")
                    ]
                ),
                self.__search_status_pill,
            ]
        )

    def did_mount(self):
        super().did_mount()
        if (self.page):
            self.page.overlay.append(self.__search_file_picker)
            self.page.overlay.append(self.__search_dir_picker)
            self.page.overlay.append(self.__output_dir_picker)

            self.__init_output_dir_to_first_input_dirname()

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
            if self.__output_dir_path.value == '':
                self.__init_output_dir_to_first_input_dirname()

    def on_pick_search_dir_button_click(self, ev: ft.ControlEvent):
        self.__search_dir_picker.get_directory_path()

    def on_search_dir_picked(self, ev: ft.FilePickerResultEvent):
        if ev.path is not None and ev.path not in self.__search_paths:
            self.__search_paths.append(ev.path)

            # set default output path when picking the first file
            if self.__output_dir_path.value == '':
                self.__init_output_dir_to_first_input_dirname()

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
        logger = get_logger()

        if not bool(self.__search_paths):
            logger.error("No search paths supplied. Aborting search operation.")
            return
        if not bool(self.__search_regex.value):
            logger.error("No string key supplied. Aborting search operation.")
            return
        if not bool(self.__output_dir_path.value):
            logger.error("Output directory not supplied. Aborting search operation.")
            return

        errored = False
        self.__search_in_progress.value = True
        for input_path in self.__search_paths:
            try:
                if os.path.isdir(input_path):
                    self.__string_key_discovery.discover_str_keys_in_directory(input_path, self.__output_dir_path.value, self.__search_regex.value)
                elif input_path.endswith('.xml'):
                    self.__string_key_discovery.discover_str_keys_in_xml(input_path, self.__output_dir_path.value, self.__search_regex.value)
                elif input_path.endswith(('.ws', '.wss')):
                    self.__string_key_discovery.discover_str_keys_in_witcherscript(input_path, self.__output_dir_path.value, self.__search_regex.value)
            except Exception as ex:
                logger.error(ex)
                logger.debug(traceback.format_exc())
                errored = True
        self.__search_in_progress.value = False

        if not errored:
            self.__search_status_pill.show("Files and/or directories searched successfully!")
        else:
            self.__search_status_pill.show("Errors occured during the search! Check the logs.", True)


    def __init_output_dir_to_first_input_dirname(self):
        # set default output path when picking the first file
        if len(self.__search_paths) > 0:
            self.__output_dir_path.value = os.path.dirname(self.__search_paths[0])