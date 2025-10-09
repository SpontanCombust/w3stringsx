import logging

import flet as ft

from w3stringsx_lib.logging import subscribe_to_logger, unsubscribe_from_logger


class _StringLogHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.all_logs = ''

    def emit(self, record: logging.LogRecord) -> None:
        self.all_logs += self.format(record) + '\n'

class LogsPanel(ft.Container):
    def __init__(
            self,
            width: ft.OptionalNumber = None,
            height: ft.OptionalNumber = None,
            bgcolor: ft.ColorValue | None = None,
            color: ft.ColorValue | None = None,
    ):
        self.__logs_handler = _StringLogHandler()
        
        super().__init__(
            width=width,
            height=height,
            bgcolor=bgcolor,
            content=ft.TextField(
                value=self.__logs_handler.all_logs,
                label='Logs go here...',
                multiline=True,
                read_only=True,
                dense=True,
                expand=True,
                min_lines=15,
                max_lines=15,
                text_size=16,
                text_style=ft.TextStyle(
                    font_family='Monospace',
                    color=color
                ),
                text_align=ft.TextAlign.START
            ),
        )

    def did_mount(self):
        super().did_mount()
        subscribe_to_logger(self.__logs_handler)

    def will_unmount(self):
        super().will_unmount()
        unsubscribe_from_logger(self.__logs_handler)
