from typing import Self, Any, Callable, TypeVar, Generic

import flet as ft

from flet_reactive.reactive_control import Reactive
from flet_reactive.state import State, ListState


C = TypeVar('C', bound=ft.Control)
class Conditional(Reactive[C]):
    def __init__(self, 
        states: list[State[Any] | ListState[Any]],
        condition: Callable[[], bool],
        true_content: C,
        false_content: C | None = None,
        on_change: Callable[[C], Any] | None = None,
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
        self.__condition = condition
        self.__true_content = true_content
        self.__false_content = false_content
        content = true_content if condition() else false_content
        super().__init__(states, content, on_change, ref, expand, expand_loose, col, opacity, tooltip, badge, visible, disabled, data, rtl)

    def _on_state_changed(self):
        self._content = self.__true_content if self.__condition() else self.__false_content
        return super()._on_state_changed()
    