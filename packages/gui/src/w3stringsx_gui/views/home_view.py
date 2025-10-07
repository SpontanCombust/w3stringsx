import flet as ft
import flet.canvas as cv
import flet_dropzone as ftd

from w3stringsx_gui.components import feature_button
from w3stringsx_gui.routing import Router, Routes


def home_view(router: Router, props: object) -> ft.View:
    assert router is not None

    return ft.View(
        route=Routes.HOME,
        controls=[
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            feature_button(
                                'icons/file-lock.svg', 
                                'ENCODE \n CSV to w3strings', 
                                on_click=lambda e: router.goto(Routes.ENCODE_STRINGS)),
                            feature_button(
                                'icons/file-lock-open.svg', 
                                'DECODE \n w3strings to CSV', 
                                on_click=lambda e: router.goto(Routes.DECODE_STRINGS)),
                            feature_button(
                                'icons/file-find.svg', 
                                'SEARCH \n for string keys', 
                                on_click=lambda e: router.goto(Routes.SEARCH_FOR_STRING_KEYS)),
                        ],
                        spacing=40,
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    ftd.Dropzone(
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
                        ),
                        on_dropped=lambda ev: print(ev.files)
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=40
            )
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        padding=100
    )