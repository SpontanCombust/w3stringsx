from typing import TypeVar, final, Callable

from flet_reactive.state_observer import StateObserver
from flet_reactive.state import State


_T = TypeVar('_T')

@final
class Effect(StateObserver[_T]):
    def __init__(self, state: State[_T], handler: Callable[[_T, _T], None]) -> None:
        self._state = state
        state.add_observer(self)
        self._handler = handler

    def on_state_changed(self, old_state: _T, new_state: _T) -> None:
        self._handler(new_state, old_state)

    def release_observed_states(self) -> None:
        self._state.remove_observer(self)

