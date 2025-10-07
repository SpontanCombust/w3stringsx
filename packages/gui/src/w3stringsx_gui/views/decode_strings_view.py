import flet as ft

from w3stringsx_gui.routing import Router, Routes


class DecodeStringsView(ft.View):
    def __init__(self, router: Router, props: object):
        super().__init__(
            route=Routes.DECODE_STRINGS,
            controls=[
                ft.AppBar(title=ft.Text("DECODING"))
            ]
        )
