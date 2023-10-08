from typing import Any


class State:
    def __init__(self, state: dict[str, Any]) -> None:
        self._state = state

    def __getattr__(self, key: str) -> Any:
        try:
            return self._state[key]
        except KeyError as exc:
            raise AttributeError(f'"State" object has no attribute "{key}"') from exc

    def __eq__(self, other: object) -> bool:
        # for tests
        return isinstance(other, State) and self._state == other._state
