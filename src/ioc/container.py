from infrastructure.django.configurator import DjangoConfigurator
from infrastructure.punq.container import AutoRegisteringContainer


class ContainerFactory:
    def __call__(
        self,
    ) -> AutoRegisteringContainer:
        container = AutoRegisteringContainer()

        # It's required to configure Django before any registrations due to model imports
        self._configure_django(container)

        self._register(container)

        return container

    def _configure_django(self, container: AutoRegisteringContainer) -> None:
        configurator = container.resolve(DjangoConfigurator)
        configurator.configure()

    def _register(self, container: AutoRegisteringContainer) -> None:
        # Import registry functions here to avoid imports before setting up Django
        from ioc.registries import Registry  # noqa: PLC0415

        registry = container.resolve(Registry)
        registry.register(container)
