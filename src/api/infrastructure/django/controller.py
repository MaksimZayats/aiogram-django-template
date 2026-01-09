from abc import ABC, abstractmethod
from collections.abc import Callable
from functools import wraps
from typing import Any, Self


class Controller(ABC):
    def __new__(cls, *_args: Any, **_kwargs: Any) -> Self:
        self = super().__new__(cls)

        _wrap_methods(self)

        return self

    @abstractmethod
    def register_routes(self, router: Any) -> None: ...


def _wrap_methods(controller: Controller) -> None:
    for attr_name in dir(controller):
        attr = getattr(controller, attr_name)
        if callable(attr) and not attr_name.startswith("_"):
            setattr(
                controller,
                attr_name,
                _wrap_route(attr),
            )


def _wrap_route[F: Callable[..., Any]](method: F) -> F:
    @wraps(method)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return method(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
