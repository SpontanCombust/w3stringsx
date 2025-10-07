import flet as ft

from w3stringsx_gui.routing import Router, Routes


def find_string_keys_view(router: Router, props: object) -> ft.View:
    return ft.View(
        route=Routes.SEARCH_FOR_STRING_KEYS,
        controls=[
            ft.AppBar(title=ft.Text("STRING KEY SEARCH"))
        ]
    )