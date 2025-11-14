from typing import Iterable, List, Self, Any, Callable, SupportsIndex, TypeVar, Generic

import flet as ft

from flet_reactive.state import State, ListState
from flet_reactive.state_observer import StateObserver, ListStateObserver


C = TypeVar('C', bound=ft.Control)
class Reactive(ft.Control, StateObserver[Any], ListStateObserver[Any], Generic[C]):
    def __init__(self, 
        states: list[State[Any] | ListState[Any]],
        content: C | None = None,
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
        super().__init__(ref, expand, expand_loose, col, opacity, tooltip, badge, visible, disabled, data, rtl)
        self.__states = states
        self._content = content
        self.__on_change = on_change

    def is_isolated(self) -> bool:
        return True

    def did_mount(self):
        super().did_mount()
        self.setup_observed_states()

    def will_unmount(self):
        super().will_unmount()
        self.release_observed_states()

    def _get_control_name(self) -> str:
        return 'flet_reactive'

    def _get_children(self) -> List[ft.Control]:
        children: list[ft.Control] = []
        if self._content:
            self._content._set_attr_internal("n", "content")
            children.append(self._content)
        return children


    def setup_observed_states(self) -> None:
        for state in self.__states:
            state.add_observer(self)
    
    def on_state_changed(self, old_state: Any, new_state: Any):
        self._on_state_changed()

    def on_set_state_item(self, key: SupportsIndex, value: Any) -> None:
        self._on_state_changed()

    def on_set_state_item_slice(self, key: slice, value: Iterable[Any]) -> None:
        self._on_state_changed()

    def on_del_state_item(self, key: SupportsIndex) -> None:
        self._on_state_changed()

    def on_del_state_item_slice(self, key: slice) -> None:
        self._on_state_changed()

    def on_insert_state_item(self, key: SupportsIndex, value: Any) -> None:
        if self.__on_change and self._content:
            self.__on_change(self._content)
        self.update()

    def release_observed_states(self) -> None:
        for state in self.__states:
            state.remove_observer(self)


    def _on_state_changed(self):
        if self.__on_change and self._content:
            self.__on_change(self._content)
        self.update()



C = TypeVar('C', bound=ft.Control)
class ReactiveBuilder(ft.Control, StateObserver[Any], Generic[C]):
    def __init__(self, 
        states: list[State[Any]],
        content_builder: Callable[[], C],
        on_after_build: Callable[[C], Any] | None = None,
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
        self.__content_builder = content_builder
        self.__content = content_builder()
        self.__on_after_build = on_after_build

    def is_isolated(self) -> bool:
        return True

    def did_mount(self):
        super().did_mount()
        self.setup_observed_states()
        
    def will_unmount(self):
        super().will_unmount()
        self.release_observed_states()

    def _get_control_name(self) -> str:
        return 'flet_reactive'

    def _get_children(self) -> List[ft.Control]:
        children: list[ft.Control] = []
        if self.__content:
            self.__content._set_attr_internal("n", "content")
            children.append(self.__content)
        return children


    def setup_observed_states(self) -> None:
        for state in self.__states:
            state.add_observer(self)

    def on_state_changed(self, old_state: Any, new_state: Any):
        self.__rebuild_content()
        if self.__on_after_build is not None:
            self.__on_after_build(self.__content)
        self.update()

    def release_observed_states(self) -> None:
        for state in self.__states:
            state.remove_observer(self)


    def __rebuild_content(self):
        self.__content = self.__content_builder()
