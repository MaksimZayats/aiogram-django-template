from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar, cast

from django.urls import URLResolver, path
from rest_framework.routers import SimpleRouter
from rest_framework.viewsets import GenericViewSet, ViewSet

T = TypeVar("T", bound=Any)


@dataclass
class CustomViewRouter:
    """Router for APIView and ViewSet."""

    url_prefix: str = ""

    _drf_router: SimpleRouter = field(default_factory=SimpleRouter)
    _paths: list[URLResolver] = field(default_factory=list)

    def register(
        self,
        route: str,
        name: str | None = None,
        basename: str | None = None,
        as_view_kwargs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Callable[[T], T]:
        route = f"{self.url_prefix}{route}"

        def decorator(view: T) -> T:
            if issubclass(view, (ViewSet, GenericViewSet)):
                kwargs.setdefault("basename", basename or name)
                self._drf_router.register(route, view, **kwargs)
            else:
                kwargs.setdefault("name", name or basename)
                self._paths.append(
                    path(route, view.as_view(**(as_view_kwargs or {})), **kwargs),
                )

            return cast(T, view)

        return decorator

    @property
    def urls(self) -> list[Any]:
        return cast(list[Any], self._paths + self._drf_router.urls)
