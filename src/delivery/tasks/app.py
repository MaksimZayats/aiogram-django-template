from delivery.tasks.events import CeleryEvents
from delivery.tasks.factories import CeleryAppFactory, TasksRegistryFactory
from ioc.container import ContainerFactory

_container_factory = ContainerFactory()
_container = _container_factory()

_events = _container.resolve(CeleryEvents)
_registry_factory = _container.resolve(TasksRegistryFactory)
_app_factory = _container.resolve(CeleryAppFactory)

# Register events & tasks
_events.register()
_registry = _registry_factory()

app = _app_factory()
