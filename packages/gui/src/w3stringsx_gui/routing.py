from typing import Callable, Any
import flet as ft

ViewFactory = Callable[..., ft.View]

class ViewRoute:
    def __init__(self, route: str, view_factory: ViewFactory) -> None:
        self.route = route
        self.view_factory = view_factory

    def create_view(self, **kwargs: Any) -> ft.View:
        return self.view_factory(**kwargs)

class Router:
    def __init__(self, page: ft.Page, routes: list[ViewRoute]) -> None:
        self.__page: ft.Page = page
        self.__page.on_route_change = self.on_route_change
        self.__page.on_view_pop = self.on_view_pop
        self.__routes: list[ViewRoute] = routes

    def goto(self, route: str):
        self.__page.go(route)   


    def on_route_change(self, ev: ft.RouteChangeEvent):
        for endpoint in self.__routes:
            if ev.route == endpoint.route:
                self.__page.views.append(
                    endpoint.create_view(router=self)
                )
                break
        self.__page.update()

    def on_view_pop(self, ev: ft.ViewPopEvent):
        if len(self.__page.views) > 1:
            self.__page.views.pop()
            top_view = self.__page.views[-1]
            self.__page.go(str(top_view.route))

class Routes:
    HOME = '/'
    ENCODE_STRINGS = '/encode'
    DECODE_STRINGS = '/decode'
    SEARCH_FOR_STRING_KEYS = '/find-keys'