from infrastructure.configurator import InfrastructureConfigurator
from infrastructure.punq.container import AutoRegisteringContainer


class ContainerFactory:
    def __call__(
        self,
        *,
        configure_infrastructure: bool = True,
    ) -> AutoRegisteringContainer:
        container = AutoRegisteringContainer()

        if configure_infrastructure:
            self._configure_infrastructure(container)

        self._register(container)

        return container

    def _configure_infrastructure(self, container: AutoRegisteringContainer) -> None:
        configurator = container.resolve(InfrastructureConfigurator)
        configurator.configure()

    def _register(self, container: AutoRegisteringContainer) -> None:
        # Import registry functions here to avoid imports before setting up Django/Infrastructure
        from ioc.registries import Registry  # noqa: PLC0415

        registry = container.resolve(Registry)
        registry.register(container)
