from typing import TypeVar

from flet_reactive.state import State


T = TypeVar('T')
def use_state(init_value: T) -> State[T]:
    return State(init_value)