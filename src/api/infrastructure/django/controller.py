from abc import ABC, abstractmethod
from collections.abc import Callable
from functools import wraps
from typing import Any, NoReturn, Self


class Controller(ABC):
    def __new__(cls, *_args: Any, **_kwargs: Any) -> Self:
        self = super().__new__(cls)

        _wrap_methods(self)

        return self

    @abstractmethod
    def register_routes(self, router: Any) -> None: ...

    def handle_exception(self, exception: Exception) -> NoReturn:
        raise exception


def _wrap_methods(controller: Controller) -> None:
    for attr_name in dir(controller):
        attr = getattr(controller, attr_name)
        if (
            callable(attr)
            and not attr_name.startswith("_")
            and attr_name not in ("register_routes", "handle_exception")
        ):
            setattr(
                controller,
                attr_name,
                _wrap_route(attr, controller=controller),
            )


def _wrap_route[F: Callable[..., Any]](method: F, controller: Controller) -> F:
    @wraps(method)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return method(*args, **kwargs)
        except Exception as e:  # noqa: BLE001
            return controller.handle_exception(e)

    return wrapper  # type: ignore[return-value]
