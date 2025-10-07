from typing import Any

import flet as ft

from w3stringsx_gui.routing import Routes


def decode_strings_view(**kwargs: Any) -> ft.View:
    return ft.View(
        route=Routes.DECODE_STRINGS,
        controls=[
            ft.AppBar(title=ft.Text("DECODING"))
        ]
    )