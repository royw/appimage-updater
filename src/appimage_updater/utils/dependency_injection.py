"""Simple dependency injection container for better testability."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, cast

T = TypeVar("T")


class DIContainer:
    """Simple dependency injection container."""

    def __init__(self) -> None:
        self._services: dict[type[Any], Callable[[], Any]] = {}
        self._singletons: dict[type[Any], Callable[[], Any]] = {}
        self._singleton_instances: dict[type[Any], Any] = {}

    def register_instance(self, service_type: type[T], instance: T) -> None:
        """Register a service instance."""
        self._services[service_type] = lambda: instance

    def register(self, service_type: type[T], factory: Callable[[], T], singleton: bool = False) -> None:
        """Register a service with its factory function."""
        self._services[service_type] = factory
        if singleton:
            self._singletons[service_type] = factory

    def get(self, service_type: type[T]) -> T:
        """Get an instance of the requested service type."""
        # Check if it's a singleton and already instantiated
        if service_type in self._singletons:
            if service_type not in self._singleton_instances:
                factory = self._singletons[service_type]
                self._singleton_instances[service_type] = factory()
            return cast(T, self._singleton_instances[service_type])

        # Regular service instantiation
        if service_type not in self._services:
            msg = f"Service {service_type} not registered"
            raise ValueError(msg)

        factory = self._services[service_type]
        return cast(T, factory())

    def has(self, service_type: type[T]) -> bool:
        """Check if a service type is registered."""
        return service_type in self._services


# Global DI container
_global_container: DIContainer | None = None


def get_container() -> DIContainer:
    """Get the global dependency injection container instance."""
    global _global_container
    if _global_container is None:
        _global_container = DIContainer()
    return _global_container
