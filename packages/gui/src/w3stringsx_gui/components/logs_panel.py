from dataclasses import dataclass
import logging
import os

import flet as ft

import flet_reactive as ftr
from w3stringsx_lib.logging import subscribe_to_logger, unsubscribe_from_logger, get_log_file_path


MAX_LOG_LINES = 200

@dataclass
class FormattedLogRecord:
    msg: str
    level: int

    def color(self) -> ft.ColorValue | None:
        if self.level >= logging.ERROR:
            return ft.Colors.RED
        elif self.level >= logging.WARNING:
            return ft.Colors.AMBER
        else:
            return None

class _StringLogHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.logs = ftr.ListState[FormattedLogRecord]([])

    def emit(self, record: logging.LogRecord) -> None:
        self.logs.append(FormattedLogRecord(
            msg=self.format(record),
            level=record.levelno
        ))

        # trim to half the expected max size when exceeded
        if len(self.logs) > MAX_LOG_LINES:
            del self.logs[:MAX_LOG_LINES // 2]

class LogsPanel(ft.Container):
    def __init__(
            self,
            width: ft.OptionalNumber = None,
            height: ft.OptionalNumber = None
    ):
        self.__vlist_view_ref = ft.Ref[ft.ListView]()
        self.__logs_handler = _StringLogHandler()
        self.__vlist_scroll_effect = ftr.ListEffect(self.__logs_handler.logs, lambda: 
            self.__vlist_view_ref.current.scroll_to(offset=-1)
        )
        
        super().__init__(
            width=width,
            height=height,
            bgcolor=ft.Colors.SURFACE,
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
                                    ft.SelectionArea(
                                        ftr.ReactiveColumn(
                                            expand=True,
                                            spacing=0,
                                            controls_data=self.__logs_handler.logs,
                                            controls_mapper=lambda record: ft.Text(
                                                value=record.msg,
                                                size=16,
                                                style=ft.TextStyle(
                                                    font_family='Monospace',
                                                    color=record.color() or ft.Colors.ON_SURFACE
                                                ),
                                                text_align=ft.TextAlign.START,
                                            ),
                                        )
                                    ),
                                ]
                            ),
                        ],
                    ),
                    ft.IconButton(
                        icon=ft.Icons.FILE_OPEN,
                        icon_color=ft.Colors.ON_SURFACE,
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
        self.__vlist_scroll_effect.release_observed_states()
        unsubscribe_from_logger(self.__logs_handler)

    def is_isolated(self) -> bool:
        return True
    
    def on_open_logs_file_button_click(self, ev: ft.ControlEvent):
        os.startfile(get_log_file_path())