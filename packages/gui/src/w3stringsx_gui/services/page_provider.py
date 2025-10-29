import flet as ft


class PageProvider:
    def __init__(self) -> None:
        self.__page: ft.Page | None = None
    
    def acquire(self, page: ft.Page):
        self.__page = page

    def provide(self) -> ft.Page:
        if self.__page is None:
            raise Exception('Page has not been set')
        return self.__page
