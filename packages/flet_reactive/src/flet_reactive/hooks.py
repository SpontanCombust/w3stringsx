from flet_reactive.state import State

def use_state[T](init_value: T) -> State[T]:
    return State(init_value)