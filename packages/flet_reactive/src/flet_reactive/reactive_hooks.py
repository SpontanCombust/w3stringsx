from typing import Any, TypeVar, Callable

import flet as ft

from flet_reactive.state import State, ListState, StateObserver, ListStateObserver
from flet_reactive.computed import Computed
from flet_reactive.effect import Effect

_T = TypeVar('_T', bound=object)


class ReactiveHooks(ft.Control):
    def __init__(self) -> None:
        super().__init__()

    def use_state(self, init_value: _T) -> State[_T]:
        return State[_T](init_value)

    def use_list_state(self, init_value: list[_T]) -> ListState[_T]:
        return ListState[_T](init_value)
    
    def use_effect(self, states: list[State[Any] | ListState[Any]], handler: Callable[[], None]) -> Effect:
        effect = Effect(states, handler)
        self.__get_state_observers().append(effect)
        return effect
    
    def use_computed(self, dependencies: list[State[Any] | ListState[Any]], resolver: Callable[[], _T]) -> Computed[_T]:
        computed = Computed[_T](dependencies, resolver)
        self.__get_state_observers().append(computed)
        return computed
    
    def will_unmount(self):
        super().will_unmount()
        state_observers = self.__get_state_observers()
        for obs in state_observers:
            obs.release_observed_states()
        state_observers.clear()

    # above functions may be used in a constructor before the super() call
    # because of this all required data must be initialized dynamically instead of traditionally in the constructor
    def __get_state_observers(self) -> list[StateObserver[Any] | ListStateObserver[Any]]:
        if not hasattr(self, '__state_observers'):
            self.__state_observers = []
        return self.__state_observers
