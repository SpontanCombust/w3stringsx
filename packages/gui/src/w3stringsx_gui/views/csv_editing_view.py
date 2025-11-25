from dataclasses import dataclass
import os
import re
from typing import cast

import flet as ft

import flet_reactive as ftr
from w3stringsx_lib.logging import get_logger
from w3stringsx_lib.localization import StringId
from w3stringsx_lib.w3strings_csv import (
    W3StringsCsvDocument, 
    W3StringsCsvDocumentLine,
    W3StringsCsvCompleteEntry,
    W3StringsCsvShortEntry,
    W3StringsCsvPlainComment,
    W3StringsCsvAttributeComment,
    W3StringsCsvEmptyLine,
)
from w3stringsx_svc import Configuration
from w3stringsx_gui.services import W3stringsxGuiConfiguration
from w3stringsx_gui.views.view_base import ViewBase
from w3stringsx_gui.routing import Routes, Router


@dataclass
class CsvEditingViewProps:
    csv_path: str | None = None

class CsvEditingView(ViewBase, ftr.ReactiveHooks):
    TITLE = "CSV EDITING"
    PROPS_TYPE = CsvEditingViewProps
    ALLOWED_EXTS = ['csv']

    def __init__(self,
        config: Configuration,
        props: CsvEditingViewProps = CsvEditingViewProps()             
    ):
        self.__config = cast(W3stringsxGuiConfiguration, config)

        self.__csv_file_path: ftr.State[str | None] = self.use_state(None)
        self.__csv_file_picker = ft.FilePicker(on_result=self.on_csv_file_picked)
        self.__show_id_column: ftr.State[bool | None] = self.use_state(self.__config.csv_editor_show_id_column.get_or_default())
        self.__show_key_hash_column: ftr.State[bool | None] = self.use_state(self.__config.csv_editor_show_key_hash_column.get_or_default())
        self.__show_comments: ftr.State[bool | None] = self.use_state(self.__config.csv_editor_show_comments.get_or_default())
        self.__csv_lines: ftr.ListState[W3StringsCsvDocumentLine] = self.use_list_state([])
        self.__should_save: ftr.State[bool | None] = self.use_state(False)

        self.__csv_file_path.value = props.csv_path
        self.use_effect([self.__should_save], self.should_save_effect)
        VISIBLE_CSV_TABLE_ROWS = 15

        super().__init__(
            route=Routes.EDIT_CSV,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ftr.ReactiveTextField(
                    icon=ft.Icons.INSERT_DRIVE_FILE,
                    value=self.__csv_file_path,
                    label="Click to choose CSV file",
                    read_only=True,
                    border_color=ft.Colors.PRIMARY,
                    on_click=self.on_csv_file_path_textfield_click,
                ),
                ft.Row(
                    controls=[
                        ftr.ReactiveCheckbox(
                            label="Show ID column",
                            value=self.__show_id_column,
                            on_change=self.on_show_id_column_checkbox_change
                        ),
                        ftr.ReactiveCheckbox(
                            label="Show key hash column",
                            value=self.__show_key_hash_column,
                            on_change=self.on_show_key_hash_column_checkbox_change
                        ),
                        ftr.ReactiveCheckbox(
                            label="Show comments and empty lines",
                            value=self.__show_comments,
                            on_change=self.on_show_comments_checkbox_change
                        ),
                    ]
                ),
                ftr.ReactiveDataTable(
                    height=750,
                    heading_row_color=ft.Colors.PRIMARY_CONTAINER,
                    heading_text_style=ft.TextStyle(color=ft.Colors.ON_PRIMARY_CONTAINER),
                    vertical_lines=ft.border.BorderSide(1, ft.Colors.PRIMARY),
                    horizontal_lines=ft.border.BorderSide(1, ft.Colors.PRIMARY),
                    # needed to zero-out spacing and margins, because colouring individual cells properly was impossible otherwise
                    column_spacing=0,
                    horizontal_margin=0,
                    border=ft.border.all(1, ft.Colors.PRIMARY),
                    sm_ratio=0.6,
                    lm_ratio=2.0,
                    columns=[
                        ftr.ReactiveDataColumn(
                            label=ft.Container(
                                padding=15,
                                content=ft.Text(
                                    value="ID",
                                    text_align=ft.TextAlign.END,
                                )
                            ),
                            size=ftr.Size.S,
                            numeric=True,
                            visible=self.__show_id_column,
                            visible_auto_update=False,
                        ),
                        ftr.ReactiveDataColumn(
                            label=ft.Container(
                                padding=15,
                                content=ft.Text(
                                    value="Key hash",
                                    text_align=ft.TextAlign.END,
                                ),
                            ),
                            size=ftr.Size.S,
                            numeric=True,
                            visible=self.__show_key_hash_column,
                            visible_auto_update=False,
                        ),
                        ftr.ReactiveDataColumn(
                            label=ft.Container(
                                padding=15,
                                content=ft.Text("Key")
                            ),
                            size=ftr.Size.M,
                        ),
                        ftr.ReactiveDataColumn(
                            label=ft.Container(
                                padding=15,
                                content=ft.Text("Text")
                            ),
                            size=ftr.Size.L,
                        ),
                    ],
                    rows_data=self.__csv_lines,
                    rows_mapper=self.__csv_line_to_row_mapper,
                    placeholder_rows_count=VISIBLE_CSV_TABLE_ROWS
                ),
                ft.Row(), # spacer
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ftr.ReactiveFilledButton(
                            icon=ft.Icons.SAVE,
                            text="Save",
                            width=300,
                            badge=self.use_computed([self.__should_save], lambda: 
                                ft.Badge(small_size=10, bgcolor=ft.Colors.ON_PRIMARY) if self.__should_save.value else None
                            ),
                            on_click=self.on_save_button_click,
                        )
                    ],
                ),
                
            ]
        )

    def __csv_line_to_row_mapper(self, line: W3StringsCsvDocumentLine) -> ftr.ReactiveDataRow:
        cells: list[ft.DataCell] = []
        color: ft.ColorValue | None = None
        visible: bool | ftr.State[bool | None] = True
        specific_row_height: int | None = None

        if isinstance(line, W3StringsCsvCompleteEntry):
            cells = [
                ftr.ReactiveDataCell(
                    visible=self.__show_id_column,
                    visible_auto_update=False,
                    content=ft.TextField(
                        value=str(line.id.id_num),
                        keyboard_type=ft.KeyboardType.NUMBER,
                        multiline=False,
                        text_align=ft.TextAlign.RIGHT,
                        content_padding=15,
                        border=ft.InputBorder.NONE,
                        border_radius=0,
                        input_filter=ft.InputFilter(regex_string=r"^[\d]+$", allow=True),
                        on_change=lambda ev: self.on_id_column_textfield_change(ev, line),
                    )
                ),
                ftr.ReactiveDataCell(
                    visible=self.__show_key_hash_column,
                    visible_auto_update=False,
                    content=ft.TextField(
                        value=line.key_hex,
                        keyboard_type=ft.KeyboardType.TEXT,
                        multiline=False,
                        text_align=ft.TextAlign.RIGHT,
                        content_padding=15,
                        border=ft.InputBorder.NONE,
                        border_radius=0,
                        input_filter=ft.InputFilter(regex_string=r"^[0-9a-fA-F]*$", allow=True),
                        on_change=lambda ev: self.on_key_hex_column_textfield_change(ev, line)
                    )
                ),
                ft.DataCell(
                    content=ft.TextField(
                        value=line.key_str,
                        keyboard_type=ft.KeyboardType.TEXT,
                        multiline=False,
                        text_align=ft.TextAlign.LEFT,
                        content_padding=15,
                        border=ft.InputBorder.NONE,
                        border_radius=0,
                        # input_filter=ft.InputFilter(regex_string=r"^[\w ]*$", allow=True), # notice space in regex
                        on_change=lambda ev: self.on_key_str_column_textfield_change(ev, line)
                    ),
                ),
                ft.DataCell(
                    content=ft.TextField(
                        value=line.text,
                        keyboard_type=ft.KeyboardType.TEXT,
                        multiline=False,
                        text_align=ft.TextAlign.LEFT,
                        text_style=ft.TextStyle(overflow=ft.TextOverflow.ELLIPSIS),
                        content_padding=15,
                        border=ft.InputBorder.NONE,
                        border_radius=0,
                        # everything allowed except the vertical bar character (because it's used as a separator in CSV)
                        input_filter=ft.InputFilter(regex_string=r"^[^|]*$", allow=True), 
                        on_change=lambda ev: self.on_text_column_textfield_change(ev, line)
                    ),
                )
            ]
        elif isinstance(line, W3StringsCsvShortEntry):
            cells = [
                ftr.ReactiveDataCell(
                    visible=self.__show_id_column,
                    visible_auto_update=False,
                    content=ft.TextField(
                        value='Auto',
                        read_only=True,
                        disabled=True,
                        multiline=False,
                        text_align=ft.TextAlign.RIGHT,
                        content_padding=15,
                        border=ft.InputBorder.NONE,
                        border_radius=0,
                        # bgcolor=ft.Colors.TERTIARY_CONTAINER,
                        # color=ft.Colors.ON_TERTIARY_CONTAINER,
                    )
                ),
                ftr.ReactiveDataCell(
                    visible=self.__show_key_hash_column,
                    visible_auto_update=False,
                    content=ft.Container(
                        padding=15,
                        alignment=ft.alignment.center_right,
                        # bgcolor=ft.Colors.TERTIARY_CONTAINER,
                    ),
                ),
                ft.DataCell(
                    content=ft.TextField(
                        value=line.key_str,
                        keyboard_type=ft.KeyboardType.TEXT,
                        multiline=False,
                        text_align=ft.TextAlign.LEFT,
                        content_padding=15,
                        border=ft.InputBorder.NONE,
                        border_radius=0,
                        on_change=lambda ev: self.on_key_str_column_textfield_change(ev, line)
                    ),
                ),
                ft.DataCell(
                    content=ft.TextField(
                        value=line.text,
                        keyboard_type=ft.KeyboardType.TEXT,
                        multiline=False,
                        text_align=ft.TextAlign.LEFT,
                        content_padding=15,
                        border=ft.InputBorder.NONE,
                        border_radius=0,
                        # everything allowed except the vertical bar character (because it's used as a separator in CSV)
                        input_filter=ft.InputFilter(regex_string=r"^[^|]*$", allow=True), 
                        on_change=lambda ev: self.on_text_column_textfield_change(ev, line)
                    ),
                )
            ]
        elif isinstance(line, W3StringsCsvAttributeComment):
            color = ft.Colors.SECONDARY_CONTAINER
            cells = [
                # make sure this is always shown in the first column
                ft.DataCell(
                    #TODO attrib edit modal
                    content=ft.Container(
                        padding=15,
                        alignment=ft.alignment.center_right,
                        content=ft.Text(
                            value=str(line),
                            color=ft.Colors.ON_SECONDARY_CONTAINER
                        )
                    ),
                ),
                ftr.ReactiveDataCell(
                    visible=self.__show_id_column,
                    visible_auto_update=False,
                    content=ft.Text()
                ),
                ftr.ReactiveDataCell(
                    visible=self.__show_key_hash_column,
                    visible_auto_update=False,
                    content=ft.Text()
                ),
                ft.DataCell(
                    content=ft.Text()
                ),
            ]
        elif isinstance(line, W3StringsCsvPlainComment):
            color = ft.Colors.TERTIARY_CONTAINER
            visible = self.__show_comments
            # specific_row_height = 100
            cells = [
                ft.DataCell(
                    content=ft.TextField(
                        value=line.comment_text,
                        keyboard_type=ft.KeyboardType.TEXT,
                        multiline=True,
                        border=ft.InputBorder.NONE,
                        border_radius=0,
                        content_padding=5,
                        prefix_text=';',
                        prefix_style=ft.TextStyle(
                            color=ft.Colors.ON_TERTIARY_CONTAINER
                        ),
                        text_style=ft.TextStyle(
                            color=ft.Colors.ON_TERTIARY_CONTAINER,
                            overflow=ft.TextOverflow.VISIBLE
                        ),
                        on_change=lambda ev: self.on_plain_comment_textfield_change(ev, line),
                    ),
                ),
                ftr.ReactiveDataCell(
                    visible=self.__show_id_column,
                    visible_auto_update=False,
                    content=ft.Text()
                ),
                ftr.ReactiveDataCell(
                    visible=self.__show_key_hash_column,
                    visible_auto_update=False,
                    content=ft.Text()
                ),
                ft.DataCell(
                    content=ft.Text()
                ),
            ]
        else:
            color = ft.Colors.TERTIARY_CONTAINER
            visible = self.__show_comments
            cells = [
                ftr.ReactiveDataCell(
                    visible=self.__show_id_column,
                    visible_auto_update=False,
                    content=ft.Text()
                ),
                ftr.ReactiveDataCell(
                    visible=self.__show_key_hash_column,
                    visible_auto_update=False,
                    content=ft.Text()
                ),
                ftr.ReactiveDataCell(
                    content=ft.Text()
                ),
                ftr.ReactiveDataCell(
                    content=ft.Text()
                ),
            ]

        return ftr.ReactiveDataRow(
            color=color,
            visible=visible,
            specific_row_height=specific_row_height,
            cells=cells,
        )
    
    def did_mount(self):
        super().did_mount()
        if self.page:
            self.page.overlay.append(self.__csv_file_picker)
            self.page.on_keyboard_event = self.on_keyboard_event
            self.page.update()
            
            # these could be set right away in the constructor HOWEVER
            # for some reason if the table initially has less visible columns than the max
            # the entire screen goes gray when you make those columns visible
            # self.__show_id_column.value = self.__config.csv_editor_show_id_column.get_or_default()
            # self.__show_key_hash_column.value = self.__config.csv_editor_show_key_hash_column.get_or_default()
            # self.__show_comments.value = self.__config.csv_editor_show_comments.get_or_default()
            self.__read_doc()
            
    def will_unmount(self):
        super().will_unmount()
        if self.page:
            self.page.overlay.remove(self.__csv_file_picker)
            self.page.on_keyboard_event = None


    def on_csv_file_path_textfield_click(self, ev: ft.ControlEvent):
        init_dir: str | None = None
        if self.__csv_file_path.value is not None:
            init_dir = os.path.dirname(self.__csv_file_path.value)
        self.__csv_file_picker.pick_files(
            initial_directory=init_dir,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=self.ALLOWED_EXTS,
            allow_multiple=False
        )

    def on_csv_file_picked(self, ev: ft.FilePickerResultEvent):
        if ev.files is not None and len(ev.files) > 0:
            self.__csv_file_path.value = ev.files[0].path
            self.__read_doc()


    def on_show_id_column_checkbox_change(self, ev: ft.ControlEvent):
        self.__config.csv_editor_show_id_column = self.__show_id_column.value
        self.__csv_lines[:] = self.__csv_lines # refreshing cell visibility

    def on_show_key_hash_column_checkbox_change(self, ev: ft.ControlEvent):
        self.__config.csv_editor_show_key_hash_column = self.__show_key_hash_column.value
        self.__csv_lines[:] = self.__csv_lines # refreshing cell visibility

    def on_show_comments_checkbox_change(self, ev: ft.ControlEvent):
        self.__config.csv_editor_show_comments = self.__show_comments.value
        self.__csv_lines[:] = self.__csv_lines # refreshing cell visibility

    def should_save_effect(self):
        self.can_pop = not self.__should_save.value
        self.on_confirm_pop = self.confirm_save_on_pop_dialog if not self.can_pop else None
        self.update()


    def on_id_column_textfield_change(self, ev: ft.ControlEvent, line: W3StringsCsvDocumentLine):
        control = cast(ft.TextField, ev.control)
        if isinstance(line, W3StringsCsvCompleteEntry):
            line.id = StringId(int(control.value or '0'))
            self.__should_save.value = True
        else:
            get_logger().error("Invalid CSV entry. Expected %s, got %s", W3StringsCsvCompleteEntry.__name__, line.__class__.__name__)

    def on_key_hex_column_textfield_change(self, ev: ft.ControlEvent, line: W3StringsCsvDocumentLine):
        control = cast(ft.TextField, ev.control)
        if isinstance(line, W3StringsCsvCompleteEntry):
            line.key_hex = (control.value or '').lower()
            self.__should_save.value = True
        else:
            get_logger().error("Invalid CSV entry. Expected %s, got %s", W3StringsCsvCompleteEntry.__name__, line.__class__.__name__)

    def on_key_str_column_textfield_change(self, ev: ft.ControlEvent, line: W3StringsCsvDocumentLine):
        control = cast(ft.TextField, ev.control)
        if isinstance(line, (W3StringsCsvCompleteEntry, W3StringsCsvShortEntry)):
            line.key_str = (control.value or '').strip()
            self.__should_save.value = True

            if len(line.key_str) > 0:
                recommended_key_form_regex = r"^[a-zA-Z0-9_]+$"
                if not re.match(recommended_key_form_regex, line.key_str):
                    control.error_text = "It is recommended to use only ASCII characters, digits and underscores for string keys"
                    control.error_style = ft.TextStyle(color=ft.Colors.AMBER)
                else:
                    control.error_text = None
                    control.error_style = None
                control.update()
            elif not bool(control.error_text):
                control.error_text = None
                control.error_style = None
                control.update()
        else:
            get_logger().error("Invalid CSV entry. Expected %s or %s, got %s", W3StringsCsvCompleteEntry.__name__, W3StringsCsvShortEntry.__name__, line.__class__.__name__)

    def on_text_column_textfield_change(self, ev: ft.ControlEvent, line: W3StringsCsvDocumentLine):
        control = cast(ft.TextField, ev.control)
        if isinstance(line, (W3StringsCsvCompleteEntry, W3StringsCsvShortEntry)):
            line.text = control.value or '' # not stripping the text as empty space sometimes can be useful
            self.__should_save.value = True
        else:
            get_logger().error("Invalid CSV entry. Expected %s or %s, got %s", W3StringsCsvCompleteEntry.__name__, W3StringsCsvShortEntry.__name__, line.__class__.__name__)

    def on_plain_comment_textfield_change(self, ev: ft.ControlEvent, line: W3StringsCsvDocumentLine):
        control = cast(ft.TextField, ev.control)
        if isinstance(line, W3StringsCsvPlainComment):
            line.comment_text = control.value or ''
            self.__should_save.value = True
        else:
            get_logger().error("Invalid CSV entry. Expected %s, got %s", W3StringsCsvPlainComment.__name__, line.__class__.__name__)


    def on_save_button_click(self, ev: ft.ControlEvent):
        self.__write_doc()
        self.__should_save.value = False

    def on_keyboard_event(self, ev: ft.KeyboardEvent):
        if ev.ctrl and ev.key.upper() == 'S':
            self.__write_doc()
            self.__should_save.value = False


    def confirm_save_on_pop_dialog(self, ev: ft.ControlEvent):
        if not self.page or not self.__csv_file_path.value:
            return
        
        import asyncio
        # calling confirm_pop immediately in AlertDialog breaks the app
        async def schedule_confirm_pop(should_pop: bool):
            await asyncio.sleep(0.1)
            self.confirm_pop(should_pop)
        
        def on_yes(ev: ft.ControlEvent):
            if not self.page:
                return
            self.page.close(confirm_dialog)
            saved = self.__write_doc()
            self.page.run_task(schedule_confirm_pop, saved)

        def on_no(ev: ft.ControlEvent):
            if not self.page:
                return
            self.page.close(confirm_dialog)
            self.page.run_task(schedule_confirm_pop, True)

        def on_cancel(ev: ft.ControlEvent):
            if not self.page:
                return
            self.page.close(confirm_dialog)

        confirm_dialog = ft.AlertDialog(
            title=ft.Text("There are unsaved changes"),
            content=ft.Text("Do you want to save changes made to " + str(os.path.basename(self.__csv_file_path.value)) + " ?"),
            actions=[
                ft.TextButton("Yes", on_click=on_yes),
                ft.TextButton("No", on_click=on_no),
                ft.TextButton("Cancel", on_click=on_cancel)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=False,
        )

        self.page.open(confirm_dialog)


    def __read_doc(self):
        if not self.page:
            return
        
        if self.__csv_file_path.value:
            csv_doc = W3StringsCsvDocument(self.__csv_file_path.value)

            try:
                csv_doc.read_from_file()
            except Exception as ex:
                self.page.open(ft.SnackBar(
                    content=ft.Text(f"{ex}"),
                    bgcolor=ft.Colors.RED,
                ))
                return

            self.__csv_lines[:] = [line for line in csv_doc.lines]
        else:
            self.__csv_lines.clear()

    def __write_doc(self) -> bool:
        if not self.page:
            return True
        
        if self.__csv_file_path.value:
            csv_doc = W3StringsCsvDocument(self.__csv_file_path.value)
            csv_doc.extend(
                [line for line in self.__csv_lines]
            )

            try:
                csv_doc.save_to_file()
                self.page.open(ft.SnackBar(
                    content=ft.Text(f"File saved"),
                    bgcolor=ft.Colors.GREEN,
                ))
            except Exception as ex:
                self.page.open(ft.SnackBar(
                    content=ft.Text(f"{ex}"),
                    bgcolor=ft.Colors.RED,
                ))
                return False
            
        return True
    
    # def __resize_textfield_to_lines(self, textfield: ft.Te)