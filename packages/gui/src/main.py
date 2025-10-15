import logging

import flet as ft

from w3stringsx_lib.logging import init_logger, set_log_level
from w3stringsx_ioc import ServiceContainer, di
from w3stringsx_svc import (
    Configuration,
    StringKeyDiscoveryService,
    W3StringsEncoderLocator, FromConfigW3stringsEncoderLocatorHandler, AppDirW3StringsEncoderLocatorHandler, PathEnvW3stringsEncoderLocatorHandler,
    W3StringsEncoder,
    W3StringsManagerService
)
from w3stringsx_gui.routing import ViewFactory, Routes, Router, ViewRoute
from w3stringsx_gui.views import (
    HomeView, 
    EncodeStringsView, 
    DecodeStringsView, 
    SearchForStringKeysView
)
from w3stringsx_gui.configuration import W3stringsxGuiConfiguration


ROUTE_MAP: dict[str, tuple[ViewFactory, str]] = {
    Routes.HOME: (HomeView, HomeView.TITLE),
    Routes.ENCODE_STRINGS: (EncodeStringsView, EncodeStringsView.TITLE),
    Routes.DECODE_STRINGS: (DecodeStringsView, DecodeStringsView.TITLE),
    Routes.SEARCH_FOR_STRING_KEYS: (SearchForStringKeysView, SearchForStringKeysView.TITLE)
}

def setup_services():
    config = W3stringsxGuiConfiguration()

    container = ServiceContainer.builder()\
        .abstract_singleton(Configuration, W3stringsxGuiConfiguration, config)\
        .singleton(W3StringsEncoder)\
        .singleton(StringKeyDiscoveryService)\
        .transitive_factory(W3StringsEncoderLocator, lambda resolver:
            W3StringsEncoderLocator()
            .with_handler(FromConfigW3stringsEncoderLocatorHandler(resolver.resolve(Configuration)))
            .with_handler(AppDirW3StringsEncoderLocatorHandler(resolver.resolve(Configuration)))
            .with_handler(PathEnvW3stringsEncoderLocatorHandler()))\
        .singleton(W3StringsManagerService)\
        .build()
    
    di.set_current(container)

    init_logger(config.app_dir.get_required())
    set_log_level(logging.INFO)

def main(page: ft.Page):
    setup_services()

    page.title = "w3stringsx GUI"
    page.window.width = 1400
    page.window.height = 900

    router = Router(page, [ViewRoute(route, view_factory, view_title) for route, (view_factory, view_title) in ROUTE_MAP.items()])
    router.goto(Routes.HOME)

ft.app(main) # type: ignore
