import logging
from typing import cast, TypeVar

import flet as ft

import flet_reactive as ftr
from w3stringsx_lib.logging import set_log_level
from w3stringsx_lib.localization import ALL_LANGS_NAME_MAP
from w3stringsx_svc import Configuration
from w3stringsx_gui.views.view_base import ViewBase
from w3stringsx_gui.services import W3stringsxGuiConfiguration
from w3stringsx_gui.routing import Routes


_T = TypeVar('_T')

class SettingsView(ViewBase):
    TITLE = "SETTINGS"

    def __init__(self,
        configuration: Configuration
    ):
        self.__config = cast(W3stringsxGuiConfiguration, configuration)

        self.__should_save = ftr.State[bool | None](False)
        self.__settings_to_save: set[object] = set()
        self.__w3strings_encoder_path = ftr.State[str | None](self.__config.w3strings_encoder_path.get())
        self.__w3strings_encoder_picker = ft.FilePicker(on_result=self.on_w3strings_encoder_picked)
        self.__theme_mode = ftr.State[str | None](self.__config.theme_mode.get_or_default())
        self.use_effect([self.__theme_mode], self.on_theme_mode_changed)
        self.__log_level: ftr.State[str | None] = self.use_state(str(self.__config.log_level.get_or_default()))
        self.use_effect([self.__log_level], self.on_log_level_changed)
        self.__default_fallback_lang: ftr.State[str | None] = self.use_state(self.__config.default_fallback_language.get_or_default())
        self.use_effect([self.__default_fallback_lang], self.on_default_fallback_lang_changed)

        self.__reset_confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Please confirm"),
            content=ft.Text("Are you sure you want to reset settings to default?"),
            actions=[
                ft.TextButton("Yes", on_click=self.on_reset_confirm_dialog_yes),
                ft.TextButton("No", on_click=self.on_reset_confirm_dialog_no),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=self.on_reset_confirm_dialog_no,
        )

        super().__init__(
            route=Routes.SETTINGS,
            spacing=15,
            controls=[
                ft.Row(
                    controls=[
                        ftr.ReactiveTextField(
                            expand=True,
                            label="Custom w3strings encoder path",
                            icon=ft.Icons.TERMINAL,
                            value=self.__w3strings_encoder_path,
                            read_only=True,
                            border_color=ft.Colors.PRIMARY,
                            on_click=self.on_w3strings_encoder_path_picker_button_click,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.ATTACH_FILE,
                            on_click=self.on_w3strings_encoder_path_picker_button_click,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLEAR,
                            on_click=self.on_w3strings_encoder_path_clear_button_click
                        )
                    ]
                ),
                ft.Row(
                    spacing=15,
                    controls=[
                        ft.Icon(
                            name=ft.Icons.PALETTE_OUTLINED,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ftr.ReactiveDropdown(
                            label="Theme mode",
                            value=self.__theme_mode,
                            border_color=ft.Colors.PRIMARY,
                            width=300,
                            options=[
                                ft.DropdownOption(
                                    key=member.value,
                                    text=member.value
                                ) for member in list(ft.ThemeMode)
                            ]
                        ),
                    ]
                ),
                ft.Row(
                    spacing=15,
                    controls=[
                        ft.Icon(
                            name=ft.Icons.ARTICLE,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ftr.ReactiveDropdown(
                            label="Log level",
                            value=self.__log_level,
                            border_color=ft.Colors.PRIMARY,
                            width=300,
                            options=[
                                ft.DropdownOption(
                                    key=str(level),
                                    text=logging.getLevelName(level)
                                ) for level in [
                                    logging.CRITICAL,
                                    logging.ERROR,
                                    logging.WARNING,
                                    logging.INFO,
                                    logging.DEBUG
                                ]
                            ]
                        ),
                    ]
                ),
                ft.Row(
                    spacing=15,
                    controls=[
                        ft.Icon(
                            name=ft.Icons.TRANSLATE,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ftr.ReactiveDropdown(
                            label="Default fallback language",
                            value=self.__default_fallback_lang,
                            border_color=ft.Colors.PRIMARY,
                            width=300,
                            menu_height=400,
                            options=[
                                ft.DropdownOption(
                                    key=lang,
                                    text=lang_name
                                ) for lang, lang_name in ALL_LANGS_NAME_MAP.items()
                            ]
                        ),
                    ]
                ),
                ft.Row(
                    height=10
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Column(
                            controls=[
                                ftr.ReactiveFilledButton(
                                    text="Save",
                                    icon=ft.Icons.SAVE,
                                    width=300,
                                    disabled=ftr.Computed([self.__should_save], lambda: not self.__should_save.value),
                                    on_click=self.on_save_button_click
                                ),
                                ft.FilledButton(
                                    text="Reset to default",
                                    icon=ft.Icons.ROTATE_LEFT,
                                    width=300,
                                    on_click=self.on_reset_button_click
                                )
                            ]
                        ),
                    ]
                )
            ],
        )

    def did_mount(self):
        super().did_mount()
        if self.page:
            self.page.overlay.append(self.__w3strings_encoder_picker)
            self.page.update()

    def will_unmount(self):
        super().will_unmount()
        if self.page:
            self.page.overlay.remove(self.__w3strings_encoder_picker)


    def on_w3strings_encoder_path_picker_button_click(self, ev: ft.ControlEvent):
        self.__w3strings_encoder_picker.pick_files(
            allowed_extensions=['exe'],
            allow_multiple=False
        )

    def on_w3strings_encoder_picked(self, ev: ft.FilePickerResultEvent):
        if ev.files is not None:
            path = ev.files[0].path
            self.__w3strings_encoder_path.value = path
            self.__update_should_save(self.__w3strings_encoder_path, self.__config.w3strings_encoder_path.get())

    def on_w3strings_encoder_path_clear_button_click(self, ev: ft.ControlEvent):
        self.__w3strings_encoder_path.value = ""
        self.__update_should_save(self.__w3strings_encoder_path, self.__config.w3strings_encoder_path.get())

    def on_theme_mode_changed(self):
        self.__update_should_save(self.__theme_mode, self.__config.theme_mode.get())

    def on_log_level_changed(self):
        config_value = self.__config.log_level.get()
        config_value_str = str(config_value) if config_value is not None else None
        self.__update_should_save(self.__log_level, config_value_str)

    def on_default_fallback_lang_changed(self):
        self.__update_should_save(self.__default_fallback_lang, self.__config.default_fallback_language.get())
        
    def on_save_button_click(self, ev: ft.ControlEvent):
        if self.page is None:
            return
        
        should_update_page = False
        if self.__w3strings_encoder_path in self.__settings_to_save:
            self.__config.w3strings_encoder_path = self.__w3strings_encoder_path.value
        if self.__theme_mode in self.__settings_to_save:
            if self.__theme_mode.value is not None:
                theme_mode = ft.ThemeMode(self.__theme_mode.value)
                self.page.theme_mode = theme_mode
                self.__config.theme_mode = theme_mode.value
            else:
                self.__config.theme_mode = None

            should_update_page = True
        if self.__log_level in self.__settings_to_save:
            self.__config.log_level = int(self.__log_level.value) if self.__log_level.value else None
            set_log_level(self.__config.log_level.get_or_default())
        if self.__default_fallback_lang in self.__settings_to_save:
            self.__config.default_fallback_language = self.__default_fallback_lang.value

        self.__settings_to_save.clear()
        self.__should_save.value = False

        self.page.open(ft.SnackBar(ft.Text("Settings saved!"), bgcolor=ft.Colors.GREEN))

        if should_update_page:
            self.page.update()

    def on_reset_button_click(self, ev: ft.ControlEvent):
        if self.page is None:
            return
        
        self.page.open(self.__reset_confirm_dialog)

    def on_reset_confirm_dialog_yes(self, ev: ft.ControlEvent):
        if self.page is None:
            return
        
        self.page.close(self.__reset_confirm_dialog)

        self.__config.reset_to_default()
        self.__w3strings_encoder_path.value = self.__config.w3strings_encoder_path.get()
        self.__theme_mode.value = self.__config.theme_mode.get_or_default()
        self.__log_level.value = str(self.__config.log_level.get_or_default())
        self.__default_fallback_lang.value = self.__config.default_fallback_language.get_or_default()
        self.__should_save.value = False
        self.__settings_to_save.clear()

        self.page.theme_mode = ft.ThemeMode(self.__config.theme_mode.get_or_default())
        set_log_level(self.__config.log_level.get_or_default())

        self.page.update()
        self.page.open(ft.SnackBar(ft.Text("Settings have been reset to default."), bgcolor=ft.Colors.AMBER))

    def on_reset_confirm_dialog_no(self, ev: ft.ControlEvent):
        if self.page is None:
            return
        
        self.page.close(self.__reset_confirm_dialog)


    def __update_should_save(self, state: ftr.State[_T], config_value: _T):
        if state.value != config_value:
            self.__settings_to_save.add(state)
        elif state in self.__settings_to_save:
            self.__settings_to_save.remove(state)
        self.__should_save.value = len(self.__settings_to_save) > 0
            