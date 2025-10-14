import logging
import os

import flet as ft

from flet_reactive import use_state, Reactive
from w3stringsx_lib.logging import subscribe_to_logger, unsubscribe_from_logger, get_log_file_path


MAX_LOG_LINES = 200

class _StringLogHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.logs = use_state('')
        self.line_count = 0

    def emit(self, record: logging.LogRecord) -> None:
        self.logs.value += '\n' + self.format(record)
        self.line_count += 1

        # trim to half the expected max size when exceeded
        if self.line_count > MAX_LOG_LINES:
            line_idx = 0
            char_idx = 0
            while line_idx < MAX_LOG_LINES // 2:
                char_idx = self.logs.value.index('\n', char_idx)
                line_idx += 1
            self.logs.value = self.logs.value[char_idx+1:]

class LogsPanel(ft.Container):
    def __init__(
            self,
            width: ft.OptionalNumber = None,
            height: ft.OptionalNumber = None,
            bgcolor: ft.ColorValue | None = ft.Colors.SECONDARY_CONTAINER,
            color: ft.ColorValue | None = ft.Colors.ON_SECONDARY_CONTAINER,
    ):
        self.__vlist_view_ref = ft.Ref[ft.ListView]()
        self.__logs_handler = _StringLogHandler()
        
        super().__init__(
            width=width,
            height=height,
            bgcolor=bgcolor,
            content=ft.Stack(
                controls=[
                    ft.ListView(
                        horizontal=True,
                        expand=True,
                        controls=[
                            ft.ListView(
                                ref=self.__vlist_view_ref,
                                horizontal=False,
                                expand=True,
                                on_scroll_interval=0,
                                controls=[
                                    Reactive(
                                        [self.__logs_handler.logs],
                                        ft.TextField(
                                            value=self.__logs_handler.logs.value,
                                            hint_text='Logs go here...',
                                            multiline=True,
                                            keyboard_type=ft.KeyboardType.MULTILINE,
                                            read_only=True,
                                            dense=True,
                                            expand=True,
                                            min_lines=15,
                                            max_lines=9999,
                                            text_size=16,
                                            text_style=ft.TextStyle(
                                                font_family='Monospace',
                                                color=color
                                            ),
                                            text_align=ft.TextAlign.START,
                                        ),
                                        on_change=lambda ctrl: (
                                            setattr(ctrl, 'value', self.__logs_handler.logs.value),
                                            self.__vlist_view_ref.current.scroll_to(offset=-1)
                                        )
                                    ),
                                ]
                            ),
                        ],
                    ),
                    ft.IconButton(
                        icon=ft.Icons.FILE_OPEN,
                        icon_color=color,
                        tooltip="Open logs file",
                        icon_size=24,
                        on_click=self.on_open_logs_file_button_click,
                        right=8,
                        top=8,
                    )
                ]
            )
        )

    def did_mount(self):
        super().did_mount()
        subscribe_to_logger(self.__logs_handler)

    def will_unmount(self):
        super().will_unmount()
        unsubscribe_from_logger(self.__logs_handler)

    def is_isolated(self) -> bool:
        return True
    
    def on_open_logs_file_button_click(self, ev: ft.ControlEvent):
        os.startfile(get_log_file_path())