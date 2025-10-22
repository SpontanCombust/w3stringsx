from typing import cast

import flet as ft
import flet.canvas as cv
import flet_dropzone.flet_dropzone as ftd

from w3stringsx_lib.file_type_relay import FileTypeRelay
from w3stringsx_lib.logging import get_logger
from w3stringsx_gui.components import FeatureButton
from w3stringsx_gui.routing import Router, Routes
from w3stringsx_gui.views.encode_strings_view import EncodeStringsView
from w3stringsx_gui.views.decode_strings_view import DecodeStringsView
from w3stringsx_gui.views.search_for_string_keys_view import SearchForStringKeysView


logger = get_logger()


class HomeView(ft.View):
    TITLE = "HOME"

    def __init__(self, router: Router, props: object):
        assert router is not None
        self.router = router

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
                            on_dropped=self.on_file_or_dir_dropped,
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

    def on_file_or_dir_dropped(self, ev: ftd.ListFiles):
        if ev.files is None or not isinstance(ev.files, list):
            return
        
        # I have absolutely no idea why the author of that widget decided to type ListFiles.files as 'float'
        files = cast(list[str], ev.files)

        if len(files) == 0:
            return


        target_route: str | None = None
        target_route_props: object | None = None

        encode_props = EncodeStringsView.PROPS_TYPE()
        def handle_encoding_files(path: str):
            nonlocal target_route
            nonlocal target_route_props

            # if multiple files get provided only one of the handlers should win over the rest
            if target_route not in (None, Routes.ENCODE_STRINGS):
                return
            
            # handle only the first encountered CSV
            if encode_props.csv_path is not None:
                return

            encode_props.csv_path = path
            target_route = Routes.ENCODE_STRINGS 
            target_route_props = encode_props

        decode_props = DecodeStringsView.PROPS_TYPE()
        def handle_decoding_files(path: str):
            nonlocal target_route
            nonlocal target_route_props

            if target_route not in (None, Routes.DECODE_STRINGS):
                return

            decode_props.w3strings_paths.append(path)
            target_route = Routes.DECODE_STRINGS
            target_route_props = decode_props

        str_search_props = SearchForStringKeysView.PROPS_TYPE()
        def handle_str_search_files(path: str):
            nonlocal target_route
            nonlocal target_route_props

            if target_route not in (None, Routes.SEARCH_FOR_STRING_KEYS):
                return

            str_search_props.search_paths.append(path)
            target_route = Routes.SEARCH_FOR_STRING_KEYS
            target_route_props = str_search_props

        relay = FileTypeRelay()\
            .register_file_handler(EncodeStringsView.ALLOWED_EXTS, handle_encoding_files)\
            .register_file_handler(DecodeStringsView.ALLOWED_EXTS, handle_decoding_files)\
            .register_file_handler(SearchForStringKeysView.ALLOWED_EXTS, handle_str_search_files)\
            .register_dir_handler(handle_str_search_files)
        
        for file in files:
            try:
                relay.relay_for_path(file, file)
            except:
                logger.warning('Tried to load a file with unsupported type: %s', file)

        if target_route is not None:
            self.router.goto(target_route, target_route_props)