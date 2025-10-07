import flet as ft


class FeatureButton(ft.ElevatedButton):
    def __init__(self, icon_src: str, text: str, on_click: ft.OptionalControlEventCallable):
        super().__init__(
            width=140,
            height=140,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=5)
            ),
            content=ft.Column(
                controls=[
                    ft.Image(
                        src=icon_src,
                        width=80,
                        height=80,
                    ),
                    ft.Text(value=text, text_align=ft.TextAlign.CENTER)
                ], 
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            on_click=on_click
        )
