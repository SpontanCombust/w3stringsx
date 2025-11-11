from typing import Sequence, Callable, Any

import flet as ft
import flet_reactive as ftr


class ViewBase(ft.View, ftr.ReactiveHooks):
    TITLE = "View"

    def __init__(self, 
        route: str | None = None, 
        controls: Sequence[ft.Control] | None = None, 
        appbar: ft.AppBar | ft.CupertinoAppBar | None = None, 
        bottom_appbar: ft.BottomAppBar | None = None, 
        floating_action_button: ft.FloatingActionButton | None = None, 
        floating_action_button_location: ft.FloatingActionButtonLocation | ft.Offset | None = None, 
        navigation_bar: ft.NavigationBar | ft.CupertinoNavigationBar | None = None, 
        drawer: ft.NavigationDrawer | None = None, 
        end_drawer: ft.NavigationDrawer | None = None, 
        vertical_alignment: ft.MainAxisAlignment | None = None, 
        horizontal_alignment: ft.CrossAxisAlignment | None = None, 
        spacing: int | float | None = None, 
        padding: int | float | ft.Padding | None = None, 
        bgcolor: str | ft.Colors | ft.CupertinoColors | None = None, 
        decoration: ft.BoxDecoration | None = None, 
        foreground_decoration: ft.BoxDecoration | None = None, 
        can_pop: bool | None = None, 
        on_confirm_pop: Callable[[ft.ControlEvent], Any] | None = None, 
        scroll: ft.ScrollMode | None = None, 
        auto_scroll: bool | None = None, 
        fullscreen_dialog: bool | None = None, 
        on_scroll_interval: int | float | None = None, 
        on_scroll: Callable[[ft.OnScrollEvent], Any] | None = None, 
        adaptive: bool | None = None
    ):
        super().__init__(
            route, 
            controls, 
            appbar, 
            bottom_appbar, 
            floating_action_button, 
            floating_action_button_location,  # type: ignore
            navigation_bar, 
            drawer, 
            end_drawer, 
            vertical_alignment, 
            horizontal_alignment, 
            spacing, 
            padding, 
            bgcolor,
            decoration, 
            foreground_decoration, 
            can_pop, 
            on_confirm_pop, 
            scroll, 
            auto_scroll, 
            fullscreen_dialog, 
            on_scroll_interval, 
            on_scroll, 
            adaptive
        )
