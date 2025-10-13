from typing import List, Self, Any, Callable

import flet as ft

from flet_reactive.state import State
from flet_reactive.state_observer import StateObserver


class Reactive(ft.Control, StateObserver[Any]):
    def __init__(self, 
        states: list[State[Any]],
        content_builder: Callable[[], ft.Control],
        on_after_build: Callable[[ft.Control], None] | None = None,
        # Control
        ref: ft.Ref[Self] | None = None, 
        expand: None | bool | int = None, 
        expand_loose: bool | None = None, 
        col: dict[str, int | float] | int | float | None = None, 
        opacity: int | float | None = None, 
        tooltip: str | ft.Tooltip | None = None, 
        badge: str | ft.Badge | None = None, 
        visible: bool | None = None, 
        disabled: bool | None = None, 
        data: Any = None, rtl: bool | None = None
    ) -> None:
        super().__init__(ref, expand, expand_loose, col, opacity, tooltip, badge, visible, disabled, data, rtl)
        self.__states = states
        for state in states:
            state.add_observer(self)

        self.__content_builder = content_builder
        self.__content = content_builder()
        self.__on_after_build = on_after_build

    def is_isolated(self) -> bool:
        return True

    def will_unmount(self):
        super().will_unmount()
        for state in self.__states:
            state.remove_observer(self)

    def _get_control_name(self) -> str:
        return 'flet_reactive'

    def _get_children(self) -> List[ft.Control]:
        children: list[ft.Control] = []
        if self.__content:
            self.__content._set_attr_internal("n", "content")
            children.append(self.__content)
        return children


    def on_state_changed(self, old_state: Any, new_state: Any):
        self.__rebuild_content()
        if self.__on_after_build is not None:
            self.__on_after_build(self.__content)
        self.update()


    def __rebuild_content(self):
        self.__content = self.__content_builder()
