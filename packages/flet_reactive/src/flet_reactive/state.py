from __future__ import annotations
from typing import Any, Iterator, SupportsIndex, TypeVar, Generic, Callable, MutableSequence, overload, final

from flet_reactive.state_observer import StateObserver, ListStateObserver


T = TypeVar('T', bound=object)


class State(Generic[T]):
    def __init__(self, init_value: T) -> None:
        self._value: T = init_value
        self._observers: list[StateObserver[T]] = []

    def __repr__(self) -> str:
        return f'<State value={self._value}>'

    @property
    def value(self) -> T:
        return self._value
    
    @value.setter
    def value(self, val: T):
        old_val = self._value
        if old_val != val:
            self._value = val
            self._notify(old_val, val)

    def add_observer(self, observer: StateObserver[T]):
        self._observers.append(observer)

    def remove_observer(self, observer: StateObserver[T]):
        self._observers.remove(observer)

    def _notify(self, old_value: T, new_value: T):
        for observer in self._observers:
            observer.on_state_changed(old_state=old_value, new_state=new_value)

@final
class ListState(MutableSequence[T]):
    def __init__(self, init_value: list[T]) -> None:
        self.__list: list[T] = init_value.copy()
        self.__observers: list[ListStateObserver[T]] = []

    # +++ MutableSequence +++
    def __contains__(self, value: object) -> bool:
        return self.__list.__contains__(value)
    
    def __iter__(self) -> Iterator[T]:
        return self.__list.__iter__()
    
    def __reversed__(self) -> Iterator[T]:
        return self.__list.__reversed__()
    
    def __len__(self) -> int:
        return self.__list.__len__()
    
    @overload
    def __getitem__(self, key: int) -> T:
        ...
    @overload
    def __getitem__(self, key: slice) -> MutableSequence[T]:
        ...
    def __getitem__(self, key) -> T | MutableSequence[T]:
        return self.__list.__getitem__(key)
    
    @overload
    def __setitem__(self, key: int, value: T) -> None:
        ...
    @overload
    def __setitem__(self, key: slice, value: MutableSequence[T]) -> None:
        ...
    def __setitem__(self, key, value): # type: ignore
        if isinstance(key, int):
            old_val = self.__list[key]
            if old_val != value:
                self.__list.__setitem__(key, value)
                self.__notify(lambda obsv: obsv.on_set_state_item(key, value))
        elif isinstance(key, slice):
            self.__list.__setitem__(key, value)
            self.__notify(lambda obsv: obsv.on_set_state_item_slice(key, value))
    
    @overload
    def __delitem__(self, key: SupportsIndex) -> None:
        ... 
    @overload
    def __delitem__(self, key: slice) -> None:
        ... 
    def __delitem__(self, key):
        if isinstance(key, SupportsIndex):
            self.__list.__delitem__(key)
            self.__notify(lambda obsv: obsv.on_del_state_item(key))
        elif isinstance(key, slice):
            self.__list.__delitem__(key)
            self.__notify(lambda obsv: obsv.on_del_state_item_slice(key))

    def insert(self, index: int, value: T):
        self.__list.insert(index, value)
        self.__notify(lambda obsv: obsv.on_insert_state_item(index, value))
    # --- MutableSequence ---


    def add_observer(self, observer: ListStateObserver[T]):
        self.__observers.append(observer)

    def remove_observer(self, observer: ListStateObserver[T]):
        self.__observers.remove(observer)

    def __notify(self, handler: Callable[[ListStateObserver[T]], None]):
        for observer in self.__observers:
            handler(observer)


class CompoundState(State[T], StateObserver[Any]):
    def __init__(self, dependencies: list[State[Any]], resolver: Callable[[], T]) -> None:
        super().__init__(resolver())

        self._dependencies = dependencies
        for dep in dependencies:
            dep.add_observer(self)

        self._resolver = resolver

    def on_state_changed(self, old_state: Any, new_state: Any) -> None:
        old_compound = self._value
        self._value = self._resolver()
        self._notify(old_compound, self._value)

    def __del__(self):
        for dep in self._dependencies:
            dep.remove_observer(self)
