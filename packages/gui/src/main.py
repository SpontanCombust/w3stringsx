import flet as ft

from w3stringsx_gui.routing import ViewFactory, Routes, Router, ViewRoute
from w3stringsx_gui.views import (
    home_view, 
    encode_strings_view, 
    decode_strings_view, 
    find_string_keys_view)


ROUTE_MAP: dict[str, ViewFactory] = {
    Routes.HOME: home_view,
    Routes.ENCODE_STRINGS: encode_strings_view,
    Routes.DECODE_STRINGS: decode_strings_view,
    Routes.SEARCH_FOR_STRING_KEYS: find_string_keys_view
}

def main(page: ft.Page):
    page.title = "w3stringsx GUI"
    router = Router(page, [ViewRoute(route, view) for route, view in ROUTE_MAP.items()])
    router.goto(Routes.HOME)

ft.app(main) # type: ignore
