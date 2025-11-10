from typing import Any, Callable, Iterable, SupportsIndex, TypeVar

from flet_reactive import ListState, ListStateObserver
from flet_reactive.state import State
from flet_reactive.state_observer import StateObserver


_T = TypeVar('_T')

class Computed(State[_T], StateObserver[Any], ListStateObserver[Any]):
    def __init__(self, dependencies: list[State[Any] | ListState[Any]], resolver: Callable[[], _T]) -> None:
        super().__init__(resolver())

        self._dependencies = dependencies
        self._resolver = resolver
        self.setup_observed_states()

    def setup_observed_states(self) -> None:
        for dep in self._dependencies:
            dep.add_observer(self)

    def on_state_changed(self, old_state: Any, new_state: Any) -> None:
        self._sync_and_notify()

    def on_set_state_item(self, key: SupportsIndex, value: Any) -> None:
        self._sync_and_notify()

    def on_set_state_item_slice(self, key: slice, value: Iterable[Any]) -> None:
        self._sync_and_notify()

    def on_del_state_item(self, key: SupportsIndex) -> None:
        self._sync_and_notify()

    def on_del_state_item_slice(self, key: slice) -> None:
        self._sync_and_notify()

    def on_insert_state_item(self, key: SupportsIndex, value: Any) -> None:
        self._sync_and_notify()

    def release_observed_states(self) -> None:
        for dep in self._dependencies:
            dep.remove_observer(self)
        self._dependencies.clear()


    def _sync_and_notify(self):
        old_compound = self._value
        self._value = self._resolver()
        self._notify(old_compound, self._value)

    def __del__(self):
        self.release_observed_states()
