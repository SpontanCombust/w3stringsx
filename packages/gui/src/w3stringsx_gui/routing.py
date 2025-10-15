from __future__ import annotations
from typing import Callable

import flet as ft

from w3stringsx_gui.components import CommonAppBar


class Router:
    def __init__(self, page: ft.Page, routes: list[ViewRoute]) -> None:
        self.__page: ft.Page = page
        self.__page.views.clear() # prime the navigation stack
        self.__page.on_route_change = self.__on_route_change
        self.__page.on_view_pop = self.__on_view_pop
        self.__view_routes: list[ViewRoute] = routes
        self.__current_route_props: object = object()
        self.__is_popping: bool = False # flag signallig if we're going back in the navigation stack

    def goto(self, route: str, props: object = object()):
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
                    self.__current_route_props = object()
                    self.__page.views.append(
                        vr.create_view(router=self, props=props)
                    )
                    break
        self.__is_popping = False
        self.__page.update()

    def __on_view_pop(self, ev: ft.ViewPopEvent):
        if len(self.__page.views) > 1:
            self.__is_popping = True
            self.__page.views.pop()
            top_view = self.__page.views[-1]
            self.__page.go(str(top_view.route))

ViewFactory = Callable[[Router, object], ft.View]

class ViewRoute:
    def __init__(self, route: str, view_factory: ViewFactory, view_title: str) -> None:
        self.route: str = route
        self.view_factory: ViewFactory = view_factory
        self.view_title: str = view_title

    def create_view(self, router: Router, props: object) -> ft.View:
        view = self.view_factory(router, props)
        view.appbar = CommonAppBar(self.view_title)
        return view


class Routes:
    HOME = '/'
    ENCODE_STRINGS = '/encode'
    DECODE_STRINGS = '/decode'
    SEARCH_FOR_STRING_KEYS = '/find-keys'