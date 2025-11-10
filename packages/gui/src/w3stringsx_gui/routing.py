from __future__ import annotations
import traceback
from typing import TypeVar, Type

import flet as ft

from w3stringsx_ioc import di
from w3stringsx_lib.logging import get_logger
from w3stringsx_gui.views.view_base import ViewBase
from w3stringsx_gui.components import CommonAppBar


class Router:
    def __init__(self, page: ft.Page, routes: list[ViewRoute]) -> None:
        self.__page: ft.Page = page
        self.__page.views.clear() # prime the navigation stack
        self.__page.on_route_change = self.__on_route_change
        self.__page.on_view_pop = self.__on_view_pop
        self.__view_routes: list[ViewRoute] = routes
        self.__current_route_props: object | None = None
        self.__is_popping: bool = False # flag signallig if we're going back in the navigation stack

    def goto(self, route: str, props: object | None = None):
        self.__current_route_props = props
        self.__page.go(route)

    @property
    def route(self) -> str:
        return self.__page.route


    def __on_route_change(self, ev: ft.RouteChangeEvent):
        if not self.__is_popping:
            for vr in self.__view_routes:
                if ev.route == vr.route:
                    props = self.__current_route_props
                    cb = di.container_builder()\
                        .transitive(vr.view_cls)\
                        .singleton(Router, self)
                    if props is not None:
                        cb = cb.singleton(props.__class__, props)
                    route_container = cb.build()
            
                    di.push_container(route_container)
                    try:
                        view = vr.create_view()
                        self.__page.views.append(view)    
                    except Exception as ex:
                        self.__page.open(ft.SnackBar(
                            content=ft.Text(str(ex), color=ft.Colors.ON_ERROR),
                            duration=10000,
                            show_close_icon=True,
                            bgcolor=ft.Colors.ERROR, 
                        ))
                        logger = get_logger()
                        logger.error(ex)
                        logger.error(traceback.format_exc())
                    di.pop_container()
                    break
        self.__current_route_props = None
        self.__is_popping = False
        self.__page.update()

    def __on_view_pop(self, ev: ft.ViewPopEvent):
        if len(self.__page.views) > 1:
            self.__is_popping = True
            self.__page.views.pop()
            top_view = self.__page.views[-1]
            self.__page.go(str(top_view.route))

_V = TypeVar('_V', bound=ViewBase)

class ViewRoute:
    def __init__(self, route: str, view_cls: Type[_V]) -> None:
        self.route: str = route
        self.view_cls = view_cls

    def create_view(self) -> ft.View:
        view = di.resolve(self.view_cls)
        view.appbar = CommonAppBar(view.TITLE)
        view.padding = ft.padding.symmetric(10, 30)
        return view


class Routes:
    HOME = '/'
    SETTINGS = '/settings'
    ENCODE_STRINGS = '/encode'
    DECODE_STRINGS = '/decode'
    SEARCH_FOR_STRING_KEYS = '/find-keys'