from dataclasses import dataclass
import logging
import os
import sys

import flet as ft

import flet_reactive as ftr
from w3stringsx_lib.logging import subscribe_to_logger, unsubscribe_from_logger, get_log_file_path


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
    def __init__(self, scrollback: int) -> None:
        super().__init__()
        self.logs = ftr.ListState[FormattedLogRecord]([])
        self.scrollback = scrollback

    def emit(self, record: logging.LogRecord) -> None:
        self.logs.append(FormattedLogRecord(
            msg=self.format(record),
            level=record.levelno
        ))

        # trim to half the expected max size when exceeded
        if len(self.logs) > self.scrollback:
            del self.logs[:self.scrollback // 2]

class LogsPanel(ftr.ReactiveContainer, ftr.ReactiveHooks):
    def __init__(
            self,
            scrollback: int,
            width: ft.OptionalNumber = None,
            height: ft.OptionalNumber = None,
            top: int | float | None = None,
            bottom: int | float | None = None,
            left: int | float | None = None,
            right: int | float | None = None,
    ):
        self.__expanded_height = height or 300
        self.__expanded: ftr.State[bool | None] = self.use_state(False)
        self.__current_height = self.use_computed(
            [self.__expanded],
            lambda: height if self.__expanded.value else 35
        )

        self.__vlist_view_ref = ft.Ref[ft.ListView]()
        self.__logs_handler = _StringLogHandler(scrollback)
        self.use_effect([self.__logs_handler.logs], lambda: 
            self.__vlist_view_ref.current.scroll_to(offset=-1)
        )
        
        super().__init__(
            width=width,
            height=self.__current_height,
            bgcolor=ft.Colors.SURFACE,
            border=ft.border.all(1, ft.Colors.SECONDARY),
            top=top,
            bottom=bottom,
            left=left,
            right=right,
            content=ft.Column(
                spacing=0,
                controls=[
                    ftr.Conditional(
                        states=[self.__expanded],
                        condition=lambda: self.__expanded.value or False,
                        true_content=ft.Row(
                            controls=[
                                ft.TextButton(
                                    icon=ft.Icons.ARROW_DROP_DOWN,
                                    text="Click to hide logs",
                                    on_click=lambda ev: self.__expanded.set_value(False),
                                    expand=True
                                )
                            ]
                        ),
                        false_content=ft.Row(
                            controls=[
                                ft.TextButton(
                                    icon=ft.Icons.ARROW_DROP_UP,
                                    text="Click to show logs",
                                    on_click=lambda ev: self.__expanded.set_value(True),
                                    expand=True
                                )
                            ]
                        )
                    ),
                    ftr.ReactiveStack(
                        height=self.__expanded_height - 40,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        visible=self.__expanded,
                        controls=[
                            ft.ListView(
                                horizontal=True,
                                padding=10,
                                controls=[
                                    ft.ListView(
                                        ref=self.__vlist_view_ref,
                                        horizontal=False,
                                        on_scroll_interval=0,
                                        controls=[
                                            ft.SelectionArea(
                                                ftr.ReactiveColumn(
                                                    spacing=0,
                                                    controls_data=self.__logs_handler.logs,
                                                    controls_mapper=lambda record, _: ft.Text(
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
                                right=8
                            )
                        ]
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
    

    @staticmethod
    def find_in_page_overlay(page: ft.Page):
        for control in page.overlay:
            if isinstance(control, LogsPanel):
                return control
        return None

    def update_scrollback(self, scrollback: int):
        self.__logs_handler.scrollback = scrollback
        

    def on_open_logs_file_button_click(self, ev: ft.ControlEvent):
        if 'win32' in sys.platform:
            os.startfile(get_log_file_path())
        elif 'linux' in sys.platform:
            import subprocess
            subprocess.call(["xdg-open", get_log_file_path()])
        else:
            raise Exception('Operation not supported on this platform')