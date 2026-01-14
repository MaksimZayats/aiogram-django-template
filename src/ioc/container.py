from punq import Container

from ioc.registries.core import register_core
from ioc.registries.delivery import register_delivery
from ioc.registries.infrastructure import register_infrastructure


def get_container() -> Container:
    container = Container()

    register_core(container)
    register_infrastructure(container)
    register_delivery(container)

    return container
