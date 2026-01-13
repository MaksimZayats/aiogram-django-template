import inspect
from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, Self

_CONTROLLER_METHODS_EXCLUDE = ("register", "handle_exception")


class Controller(ABC):
    def __new__(cls, *_args: Any, **_kwargs: Any) -> Self:
        self = super().__new__(cls)

        _wrap_methods(self)

        return self

    @abstractmethod
    def register(self, registry: Any) -> None: ...

    def handle_exception(self, exception: Exception) -> Any:
        raise exception


class AsyncController(ABC):
    def __new__(cls, *_args: Any, **_kwargs: Any) -> Self:
        self = super().__new__(cls)

        _wrap_async_methods(self)

        return self

    @abstractmethod
    def register(self, registry: Any) -> None: ...

    async def handle_exception(self, exception: Exception) -> Any:
        raise exception


def _wrap_methods(controller: Controller) -> None:
    for attr_name in dir(controller):
        attr = getattr(controller, attr_name)
        if (
            callable(attr)
            and not attr_name.startswith("_")
            and attr_name not in _CONTROLLER_METHODS_EXCLUDE
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


def _wrap_async_methods(controller: AsyncController) -> None:
    for attr_name in dir(controller):
        attr = getattr(controller, attr_name)
        if (
            inspect.iscoroutinefunction(attr)
            and not attr_name.startswith("_")
            and attr_name not in _CONTROLLER_METHODS_EXCLUDE
        ):
            setattr(
                controller,
                attr_name,
                _wrap_async_route(attr, controller=controller),
            )


def _wrap_async_route[F: Callable[..., Coroutine[Any, Any, Any]]](
    method: F,
    controller: AsyncController,
) -> F:
    @wraps(method)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await method(*args, **kwargs)
        except Exception as e:  # noqa: BLE001
            return await controller.handle_exception(e)

    return wrapper  # type: ignore[return-value]
