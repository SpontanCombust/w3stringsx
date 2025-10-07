import flet as ft
import flet.canvas as cv

from w3stringsx_gui.components import feature_button

def home_screen() -> ft.Control:
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        feature_button('icons/file-lock.svg', 'ENCODE \n CSV to w3strings', on_click=None),
                        feature_button('icons/file-lock-open.svg', 'DECODE \n w3strings to CSV', on_click=None),
                        feature_button('icons/file-find.svg', 'FIND \n string keys', on_click=None),
                    ],
                    spacing=40,
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Text(value='OR', size=16, weight=ft.FontWeight.BOLD),
                ft.DragTarget(
                    content=ft.Stack(
                        controls=[
                            cv.Canvas(
                                shapes=[
                                    cv.Path(
                                        elements=[
                                            cv.Path.MoveTo(-200, -75),
                                            cv.Path.LineTo(200, -75),
                                            cv.Path.LineTo(200, 75),
                                            cv.Path.LineTo(-200, 75),
                                            cv.Path.LineTo(-200, -75),
                                        ],
                                        paint=ft.Paint(
                                            style=ft.PaintingStyle.STROKE,
                                            stroke_width=2,
                                            stroke_dash_pattern=[10,5]
                                        )
                                    )
                                ],
                            ),
                            ft.Text(value='Drag and drop a file here \n to deduce action automatically', size=16, text_align=ft.TextAlign.CENTER)
                        ],
                        width=400,
                        height=150,
                        alignment=ft.alignment.center
                    )
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=40
        ),
        alignment=ft.alignment.center,
        expand=True,
        padding=100
    )