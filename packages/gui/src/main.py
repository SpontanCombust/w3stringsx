import flet as ft

from w3stringsx_gui.views import *


def main(page: ft.Page):
    page.title = "w3stringsx GUI"

    page.add(home_screen())


ft.app(main) # type: ignore
