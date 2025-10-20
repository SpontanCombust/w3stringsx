from typing import TypeVar, Protocol, Iterable, SupportsIndex


T = TypeVar('T', contravariant=True)


class StateObserver(Protocol[T]):
    def on_state_changed(self, old_state: T, new_state: T) -> None:
        ...

    def release_observed_states(self) -> None:
        ...

class ListStateObserver(Protocol[T]):
    def on_set_state_item(self, key: SupportsIndex, value: T) -> None:
        ...

    def on_set_state_item_slice(self, key: slice, value: Iterable[T]) -> None:
        ...

    def on_del_state_item(self, key: SupportsIndex) -> None:
        ...

    def on_del_state_item_slice(self, key: slice) -> None:
        ...
    
    def on_insert_state_item(self, key: SupportsIndex, value: T) -> None:
        ...

    def release_observed_states(self) -> None:
        ...
