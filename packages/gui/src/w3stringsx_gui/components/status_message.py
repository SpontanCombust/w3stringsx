import asyncio

import flet as ft

from flet_reactive import Reactive, Conditional, State


class StatusMessage(Reactive):
    def __init__(self, status_state: State[bool | None], success_msg: str, error_msg: str):
        self.__status_state = status_state

        super().__init__(
            [status_state], 
            on_change=self.on_status_change,
            content=ft.Container(
                opacity=0.0,
                animate_opacity=200,
                alignment=ft.alignment.center,                
                content=Conditional(
                    [self.__status_state],
                    condition=lambda: self.__status_state.value is True,
                    true_content=ft.Container(
                        width=400,
                        padding=5,
                        bgcolor=ft.Colors.GREEN_100,
                        border_radius=20,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(
                                    name=ft.Icons.CHECK,
                                    color=ft.Colors.GREEN
                                ),
                                ft.Text(
                                    value=success_msg,
                                    color=ft.Colors.GREEN
                                ),
                            ]
                        )
                    ),
                    false_content=ft.Container(
                        width=400,
                        padding=5,
                        bgcolor=ft.Colors.RED_100,
                        border_radius=20,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(
                                    name=ft.Icons.CLEAR,
                                    color=ft.Colors.RED
                                ),
                                ft.Text(
                                    value=error_msg,
                                    color=ft.Colors.RED
                                ),
                            ]
                        )
                    ),
                ),
            ),
        )
    
    def on_status_change(self, ctrl: ft. Container):

        if self.__status_state.value is not None:
            ctrl.opacity = 1.0
            if self.__status_state.value is True and self.page:
                async def delay_transparent():
                    await asyncio.sleep(3)
                    ctrl.opacity = 0.0
                    ctrl.update()
                self.page.run_task(delay_transparent)
        else:
            ctrl.opacity = 0.0