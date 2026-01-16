from typing import TYPE_CHECKING, cast

from ioc.container import ContainerFactory

if TYPE_CHECKING:
    from delivery.http.factories import FastAPIFactory

_container_factory = ContainerFactory()
_container = _container_factory()

_api_factory = cast("FastAPIFactory", _container.resolve("FastAPIFactory"))

app = _api_factory(include_admin=True)
