from typing import Iterable, SupportsIndex, TypeVar, final, Callable

from flet_reactive.state_observer import StateObserver, ListStateObserver
from flet_reactive.state import State, ListState


_T = TypeVar('_T')

@final
class Effect(StateObserver[_T]):
    def __init__(self, state: State[_T], handler: Callable[[], None]) -> None:
        self._state = state
        self._handler = handler
        self.setup_observed_states()

    def setup_observed_states(self) -> None:
        self._state.add_observer(self)

    def on_state_changed(self, old_state: _T, new_state: _T) -> None:
        self._handler()

    def release_observed_states(self) -> None:
        self._state.remove_observer(self)

@final
class ListEffect(ListStateObserver[_T]):
    def __init__(self, state: ListState[_T], handler: Callable[[], None]) -> None:
        self._state = state
        self._handler = handler
        self.setup_observed_states()

    def setup_observed_states(self) -> None:
        self._state.add_observer(self)

    def release_observed_states(self) -> None:
        self._state.remove_observer(self)

    def on_set_state_item(self, key: SupportsIndex, value: _T) -> None:
        self._handler()

    def on_set_state_item_slice(self, key: slice, value: Iterable[_T]) -> None:
        self._handler()

    def on_del_state_item(self, key: SupportsIndex) -> None:
        self._handler()

    def on_del_state_item_slice(self, key: slice) -> None:
        self._handler()

    def on_insert_state_item(self, key: SupportsIndex, value: _T) -> None:
        self._handler()

