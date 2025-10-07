import flet as ft

from w3stringsx_gui.routing import ViewFactory, Routes, Router, ViewRoute
from w3stringsx_gui.views import (
    HomeView, 
    EncodeStringsView, 
    DecodeStringsView, 
    SearchForStringKeysView)


ROUTE_MAP: dict[str, ViewFactory] = {
    Routes.HOME: HomeView,
    Routes.ENCODE_STRINGS: EncodeStringsView,
    Routes.DECODE_STRINGS: DecodeStringsView,
    Routes.SEARCH_FOR_STRING_KEYS: SearchForStringKeysView
}

def main(page: ft.Page):
    page.title = "w3stringsx GUI"
    router = Router(page, [ViewRoute(route, view_factory) for route, view_factory in ROUTE_MAP.items()])
    router.goto(Routes.HOME)

ft.app(main) # type: ignore
