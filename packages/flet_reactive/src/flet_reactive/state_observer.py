from abc import ABC, abstractmethod


class StateObserver[T](ABC):
    @abstractmethod
    def on_state_changed(self, old_state: T, new_state: T):
        pass
    