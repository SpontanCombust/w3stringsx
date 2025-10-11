from typing import TypeVar, Generic

from flet_reactive.state_observer import StateObserver


T = TypeVar('T')
class State(Generic[T]):
    def __init__(self, init_value: T) -> None:
        self.__value: T = init_value
        self.__observers: list[StateObserver[T]] = []

    @property
    def value(self) -> T:
        return self.__value
    
    @value.setter
    def value(self, val: T):
        old_val = self.__value
        if old_val != val:
            self.__value = val
            self.__notify(old_val, val)

    def add_observer(self, observer: StateObserver[T]):
        self.__observers.append(observer)

    def remove_observer(self, observer: StateObserver[T]):
        self.__observers.remove(observer)

    def __notify(self, old_value: T, new_value: T):
        for observer in self.__observers:
            observer.on_state_changed(old_state=old_value, new_state=new_value)


