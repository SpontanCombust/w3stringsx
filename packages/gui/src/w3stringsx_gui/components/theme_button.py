from typing import cast

import flet as ft

from w3stringsx_ioc import di
from w3stringsx_svc import Configuration
from w3stringsx_gui.services import W3stringsxGuiConfiguration

class ThemeButton(ft.IconButton):
    def __init__(self,
        config = di.inject(Configuration)
    ):
        self.__config = cast(W3stringsxGuiConfiguration, config.resolve())

        super().__init__(
            tooltip="Click to change the theme mode",
            on_click=self.on_theme_change
        )

    def did_mount(self):
        self.__set_icon()
        self.update()

    def on_theme_change(self, ev: ft.ControlEvent):
        if self.page:
            theme_mode = self.page.theme_mode
            if theme_mode == ft.ThemeMode.SYSTEM:
                if self.page.platform_brightness == ft.Brightness.DARK:
                    theme_mode = ft.ThemeMode.DARK
                else:
                    theme_mode = ft.ThemeMode.LIGHT
                    
            if theme_mode == ft.ThemeMode.LIGHT:
                self.page.theme_mode = ft.ThemeMode.DARK
            else:
                self.page.theme_mode = ft.ThemeMode.LIGHT

            self.__config.theme_mode = self.page.theme_mode.value
            self.__set_icon()
            self.page.update()

    def __set_icon(self):
        if self.page and self.page.theme_mode is ft.ThemeMode.LIGHT:
            self.icon = ft.Icons.LIGHT_MODE
        else:
            self.icon = ft.Icons.DARK_MODE
