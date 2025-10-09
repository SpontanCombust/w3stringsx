import flet as ft
import flet.canvas as cv
import flet_dropzone as ftd

from w3stringsx_gui.components import FeatureButton
from w3stringsx_gui.routing import Router, Routes


class HomeView(ft.View):
    def __init__(self, router: Router, props: object):
        assert router is not None

        super().__init__(
            route=Routes.HOME,
            controls=[
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                FeatureButton(
                                    'icons/file-lock.svg', 
                                    'ENCODE \n CSV to w3strings',
                                    bgcolor=ft.Colors.PRIMARY,
                                    color=ft.Colors.ON_PRIMARY,
                                    on_click=lambda e: router.goto(Routes.ENCODE_STRINGS)),
                                FeatureButton(
                                    'icons/file-lock-open.svg', 
                                    'DECODE \n w3strings to CSV', 
                                    bgcolor=ft.Colors.PRIMARY,
                                    color=ft.Colors.ON_PRIMARY,
                                    on_click=lambda e: router.goto(Routes.DECODE_STRINGS)),
                                FeatureButton(
                                    'icons/file-find.svg', 
                                    'SEARCH \n for string keys', 
                                    bgcolor=ft.Colors.PRIMARY,
                                    color=ft.Colors.ON_PRIMARY,
                                    on_click=lambda e: router.goto(Routes.SEARCH_FOR_STRING_KEYS)),
                            ],
                            spacing=40,
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        ft.Text("OR", size=16, weight=ft.FontWeight.BOLD),
                        ftd.Dropzone(
                            content=ft.Container(
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
                                        ft.Text(
                                            value='Drag and drop a file here \n to deduce action automatically', 
                                            size=16, 
                                            text_align=ft.TextAlign.CENTER,
                                            color=ft.Colors.ON_PRIMARY_CONTAINER
                                        )
                                    ],
                                    width=400,
                                    height=150,
                                    alignment=ft.alignment.center,
                                ),
                                bgcolor=ft.Colors.PRIMARY_CONTAINER
                            ),
                            on_dropped=lambda ev: print(ev.files),
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20
                )
            ],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            padding=100
        )
