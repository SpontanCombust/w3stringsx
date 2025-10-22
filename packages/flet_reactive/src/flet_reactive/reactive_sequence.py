from typing import Any, Callable, Generic, Iterable, Iterator, SupportsIndex, TypeVar, Sequence, overload

import flet as ft

from flet_reactive.state import ListState
from flet_reactive.state_observer import ListStateObserver


T = TypeVar('T')
C = TypeVar('C', bound=ft.Control)


class ReactiveSequence(Generic[T, C], ListStateObserver[T], Sequence[C]):
    def __init__(self, 
        state: ListState[T],
        control_mapper: Callable[[T], C]
    ) -> None:
        self.__state = state
        self.__control_mapper = control_mapper
        self._controls = list[C]()

        for el in self.__state:
            self._controls.append(self.__control_mapper(el))

        self.setup_observed_states()


    def __del__(self):
        self.release_observed_states()

    #+++ Sequence +++
    def __contains__(self, value: object) -> bool:
        return self._controls.__contains__(value)
    
    def __iter__(self) -> Iterator[C]:
        return self._controls.__iter__()
    
    def __reversed__(self):
        return self._controls.__reversed__()
    
    def __len__(self) -> int:
        return self._controls.__len__()
    
    @overload
    def __getitem__(self, i: SupportsIndex, /) -> T:
        ...
    @overload
    def __getitem__(self, s: slice, /) -> Sequence[T]:
        ...
    def __getitem__(self, index): #type: ignore
        return self._controls.__getitem__(index)
    #--- Sequence ---

    #+++ ListStateObserver +++
    def setup_observed_states(self) -> None:
        self.__state.add_observer(self)
    
    def on_set_state_item(self, key: SupportsIndex, value: T) -> None:
        self._controls.__setitem__(key, self.__control_mapper(value))

    def on_set_state_item_slice(self, key: slice, value: Iterable[T]) -> None:
        self._controls.__setitem__(key, [self.__control_mapper(value) for value in value])

    def on_del_state_item(self, key: SupportsIndex) -> None:
        self._controls.__delitem__(key)

    def on_del_state_item_slice(self, key: slice) -> None:
        self._controls.__delitem__(key)
    
    def on_insert_state_item(self, key: SupportsIndex, value: T) -> None:
        self._controls.insert(key, self.__control_mapper(value))

    def release_observed_states(self) -> None:
        self.__state.remove_observer(self)

    #--- ListStateObserver ---

    