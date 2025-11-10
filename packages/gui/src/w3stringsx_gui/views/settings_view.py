from typing import Any, cast

import flet as ft

import flet_reactive as ftr
from w3stringsx_svc import Configuration
from w3stringsx_gui.services import W3stringsxGuiConfiguration
from w3stringsx_gui.routing import Routes


class SettingsView(ft.View):
    TITLE = "SETTINGS"

    def __init__(self,
        configuration: Configuration
    ):
        self.__config = cast(W3stringsxGuiConfiguration, configuration)

        self.__should_save = ftr.State[bool | None](False)
        self.__settings_to_save: set[object] = set()
        self.__w3strings_encoder_path = ftr.State[str | None](self.__config.w3strings_encoder_path.get())
        self.__w3strings_encoder_picker = ft.FilePicker(on_result=self.on_w3strings_encoder_picked)
        self.__theme_mode = ftr.State[str | None](self.__config.theme_mode.get() or ft.ThemeMode.SYSTEM.value)
        self.__theme_change_effect = ftr.Effect(self.__theme_mode, self.on_theme_mode_changed)

        super().__init__(
            route=Routes.SETTINGS,
            spacing=15,
            controls=[
                ft.Row(
                    controls=[
                        ftr.ReactiveTextField(
                            expand=True,
                            label="w3strings encoder path",
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
                            icon=ft.Icons.CANCEL,
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
                    height=10
                ),
                ftr.ReactiveFilledButton(
                    text="Save",
                    icon=ft.Icons.SAVE,
                    width=100,
                    disabled=ftr.CompoundState([self.__should_save], lambda: not self.__should_save.value),
                    on_click=self.on_save_button_click
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
        self.__theme_change_effect.release_observed_states()


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
        
    def on_save_button_click(self, ev: ft.ControlEvent):
        if self.page is None:
            return
        
        should_update_page = False
        if self.__w3strings_encoder_path in self.__settings_to_save:
            self.__config.w3strings_encoder_path = self.__w3strings_encoder_path.value or ""
        if self.__theme_mode in self.__settings_to_save:
            theme_mode = ft.ThemeMode(self.__theme_mode.value) if self.__theme_mode.value is not None else ft.ThemeMode.SYSTEM
            self.page.theme_mode = theme_mode
            self.__config.theme_mode = theme_mode.value
            should_update_page = True

        self.__settings_to_save.clear()
        self.__should_save.value = False

        self.page.open(ft.SnackBar(ft.Text("Settings saved!"), bgcolor=ft.Colors.GREEN))

        if should_update_page:
            self.page.update()


    def __update_should_save(self, state: ftr.State, config_value: Any):
        if state.value != config_value:
            self.__settings_to_save.add(state)
        else:
            self.__settings_to_save.remove(state)
        self.__should_save.value = len(self.__settings_to_save) > 0
            