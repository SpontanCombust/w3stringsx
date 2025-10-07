import flet as ft

from w3stringsx_gui.routing import Router, Routes


class EncodeStringsView(ft.View):
    def __init__(self, router: Router, props: object):
        super().__init__(
            route=Routes.ENCODE_STRINGS,
            controls=[
                ft.AppBar(title=ft.Text("ENCODING"))
            ]
        )
