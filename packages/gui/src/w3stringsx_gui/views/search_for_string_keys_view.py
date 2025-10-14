import flet as ft

from w3stringsx_gui.routing import Router, Routes
from w3stringsx_gui.components import ThemeButton


class SearchForStringKeysView(ft.View):
    def __init__(self, router: Router, props: object):
        super().__init__(
            route=Routes.SEARCH_FOR_STRING_KEYS,
            controls=[
                ft.AppBar(title=ft.Text("STRING KEY SEARCH"), actions=[ThemeButton()])
            ]
        )