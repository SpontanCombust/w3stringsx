import flet as ft


def feature_button(icon_src: str, text: str, on_click: ft.OptionalControlEventCallable) -> ft.Control:
    return ft.ElevatedButton(
        width=130,
        height=130,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=5)
        ),
        content=ft.Column(
            controls=[
                ft.Image(
                    src=icon_src,
                    width=80,
                    height=80,
                    fit=ft.ImageFit.FILL
                ),
                ft.Text(value=text, text_align=ft.TextAlign.CENTER)
            ], 
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            
        on_click=on_click
    )