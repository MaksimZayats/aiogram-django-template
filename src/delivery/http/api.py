from ninja import NinjaAPI

from ioc.container import get_container

_container = get_container()

api = _container.resolve(NinjaAPI)
