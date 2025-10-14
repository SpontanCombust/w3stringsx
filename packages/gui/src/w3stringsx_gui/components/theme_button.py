import flet as ft


class ThemeButton(ft.IconButton):
    def __init__(self):
        super().__init__(
            tooltip="Click to change the theme mode",
            on_click=self.on_theme_change
        )

    def did_mount(self):
        self.__set_icon()
        self.update()

    def on_theme_change(self, ev: ft.ControlEvent):
        if self.page:
            if self.page.theme_mode is ft.ThemeMode.LIGHT:
                self.page.theme_mode = ft.ThemeMode.DARK
            else:
                self.page.theme_mode = ft.ThemeMode.LIGHT
            self.__set_icon()
            self.page.update()

    def __set_icon(self):
        if self.page and self.page.theme_mode is ft.ThemeMode.LIGHT:
            self.icon = ft.Icons.LIGHT_MODE
        else:
            self.icon = ft.Icons.DARK_MODE
