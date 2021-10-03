"""Type hints definitions."""

from typing import Any, Callable, Dict, Protocol, Union

DefaultsType = Dict[str, Union[Callable[[], Any], float]]


class AnyFunction(Protocol):
    def __call__(self, arg: Any) -> Any:
        pass


class KwargFunction(Protocol):
    def __call__(self, *args, **kwargs: Any) -> Any:
        pass
