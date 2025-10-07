import flet as ft

from w3stringsx_gui.routing import Router, Routes


def decode_strings_view(router: Router, props: object) -> ft.View:
    return ft.View(
        route=Routes.DECODE_STRINGS,
        controls=[
            ft.AppBar(title=ft.Text("DECODING"))
        ]
    )