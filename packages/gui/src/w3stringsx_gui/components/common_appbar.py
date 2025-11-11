import flet as ft

from w3stringsx_gui.components import ThemeButton


class CommonAppBar(ft.AppBar):
    def __init__(self, title: str):
        super().__init__(
            title=ft.Text(title), actions=[ThemeButton()]
        )