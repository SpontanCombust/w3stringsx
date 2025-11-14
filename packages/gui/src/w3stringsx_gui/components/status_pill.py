import asyncio

import flet as ft

import flet_reactive as ftr


class StatusPill(ftr.ReactiveContainer, ftr.ReactiveHooks):
    def __init__(self):
        self.__visible: ftr.State[bool] = self.use_state(False)
        self.__is_error: ftr.State[bool] = self.use_state(False)
        self.__text_value: ftr.State[str | None] = self.use_state('')
        self.use_effect([self.__visible], self.__delayed_fadeout_effectt)

        super().__init__(
            opacity=self.use_computed([self.__visible], lambda:
                1.0 if self.__visible.value is True else 0.0
            ),
            disabled=self.use_computed([self.__visible], lambda:
                True if not self.__visible.value else False
            ),
            animate_opacity=200,
            alignment=ft.alignment.center,
            on_click=lambda ev: self.__dismiss(),
            content=ftr.ReactiveContainer(
                width=400,
                padding=5,
                bgcolor=self.use_computed([self.__is_error], lambda:
                    ft.Colors.RED_100 if self.__is_error.value else ft.Colors.GREEN_100
                ),
                border_radius=20,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ftr.ReactiveIcon(
                            name=self.use_computed([self.__is_error], lambda:
                                ft.Icons.CLEAR if self.__is_error.value else ft.Icons.CHECK
                            ),
                            color=self.use_computed([self.__is_error], lambda:
                                ft.Colors.RED if self.__is_error.value else ft.Colors.GREEN
                            )
                        ),
                        ftr.ReactiveText(
                            value=self.__text_value,
                            color=self.use_computed([self.__is_error], lambda:
                                ft.Colors.RED if self.__is_error.value else ft.Colors.GREEN                             
                            )
                        ),
                    ]
                )
            ),
        )

    def show(self, message: str, is_error: bool = False):
        self.__text_value.value = message
        self.__is_error.value = is_error
        self.__visible.value = True

    def __delayed_fadeout_effectt(self):
        if self.page is None:
            return

        if self.__is_error.value is False:
            async def delay_transparent():
                await asyncio.sleep(3)
                self.__visible.value = False
            self.page.run_task(delay_transparent)

    def __dismiss(self):
        self.__visible.value = False