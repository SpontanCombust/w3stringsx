from abc import ABC, abstractmethod
from typing import TypeVar, Generic


T = TypeVar('T')
class StateObserver(ABC, Generic[T]):
    @abstractmethod
    def on_state_changed(self, old_state: T, new_state: T):
        pass
    