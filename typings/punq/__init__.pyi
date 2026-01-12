from collections.abc import Callable
from enum import Enum
from typing import Any, overload

class MissingDependencyException(Exception): ...  # noqa: N818
class MissingDependencyError(MissingDependencyException): ...
class InvalidRegistrationException(Exception): ...  # noqa: N818
class InvalidRegistrationError(InvalidRegistrationException): ...
class InvalidForwardReferenceException(Exception): ...  # noqa: N818
class InvalidForwardReferenceError(InvalidForwardReferenceException): ...

class Scope(Enum):
    transient = 0
    singleton = 1

class _Empty: ...

empty: _Empty

class Container:
    def __init__(self) -> None: ...
    @overload
    def register[T](
        self,
        service: type[T],
        factory: Callable[..., T] = ...,
        *,
        scope: Scope = ...,
        **kwargs: Any,
    ) -> Container: ...
    @overload
    def register[T](
        self,
        service: type[T],
        *,
        instance: T,
        scope: Scope = ...,
        **kwargs: Any,
    ) -> Container: ...
    @overload
    def register[T](
        self,
        service: type[T],
        *,
        scope: Scope = ...,
        **kwargs: Any,
    ) -> Container: ...
    @overload
    def register(
        self,
        service: Any,
        factory: Any = ...,
        instance: Any = ...,
        scope: Scope = ...,
        **kwargs: Any,
    ) -> Container: ...
    def resolve[T](self, service_key: type[T], **kwargs: Any) -> T: ...
    def resolve_all[T](self, service: type[T], **kwargs: Any) -> list[T]: ...
    def instantiate[T](self, service_key: type[T], **kwargs: Any) -> T: ...
