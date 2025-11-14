from typing import Iterable, SupportsIndex, final, Callable, Any

from flet_reactive.state_observer import StateObserver, ListStateObserver
from flet_reactive.state import State, ListState


@final
class Effect(StateObserver[Any], ListStateObserver[Any]):
    def __init__(self, states: list[State[Any] | ListState[Any]], handler: Callable[[], None]) -> None:
        self._states = states
        self._handler = handler
        self.setup_observed_states()

    def setup_observed_states(self) -> None:
        for state in self._states:
            state.add_observer(self)
    
    def release_observed_states(self) -> None:
        for state in self._states:
            state.remove_observer(self)
        self._states.clear()

    def on_state_changed(self, old_state: Any, new_state: Any) -> None:
        self._handler()

    def on_set_state_item(self, key: SupportsIndex, value: Any) -> None:
        self._handler()

    def on_set_state_item_slice(self, key: slice, value: Iterable[Any]) -> None:
        self._handler()

    def on_del_state_item(self, key: SupportsIndex) -> None:
        self._handler()

    def on_del_state_item_slice(self, key: slice) -> None:
        self._handler()

    def on_insert_state_item(self, key: SupportsIndex, value: Any) -> None:
        self._handler()
