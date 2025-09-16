"""Tests for dependency injection container."""

import pytest

from appimage_updater.dependency_injection import DIContainer, get_container


class MockService:
    """Mock service for testing."""

    def __init__(self, value: str = "test"):
        self.value = value


class MockSingletonService:
    """Mock singleton service for testing."""

    def __init__(self):
        self.instance_id = id(self)


class TestDIContainer:
    """Test cases for DIContainer."""

    def test_register_and_get_service(self):
        """Test basic service registration and retrieval."""
        container = DIContainer()

        # Register service
        container.register(MockService, lambda: MockService("hello"))

        # Get service
        service = container.get(MockService)
        assert isinstance(service, MockService)
        assert service.value == "hello"

    def test_register_instance(self):
        """Test registering a service instance."""
        container = DIContainer()
        instance = MockService("instance")

        # Register instance
        container.register_instance(MockService, instance)

        # Get service should return same instance
        service = container.get(MockService)
        assert service is instance
        assert service.value == "instance"

    def test_singleton_service(self):
        """Test singleton service registration."""
        container = DIContainer()

        # Register as singleton
        container.register(MockSingletonService, MockSingletonService, singleton=True)

        # Get service multiple times
        service1 = container.get(MockSingletonService)
        service2 = container.get(MockSingletonService)

        # Should be same instance
        assert service1 is service2
        assert service1.instance_id == service2.instance_id

    def test_non_singleton_service(self):
        """Test non-singleton service registration."""
        container = DIContainer()

        # Register as non-singleton
        container.register(MockSingletonService, MockSingletonService, singleton=False)

        # Get service multiple times
        service1 = container.get(MockSingletonService)
        service2 = container.get(MockSingletonService)

        # Should be different instances
        assert service1 is not service2
        assert service1.instance_id != service2.instance_id

    def test_has_service(self):
        """Test checking if service is registered."""
        container = DIContainer()

        # Initially not registered
        assert not container.has(MockService)

        # Register service
        container.register(MockService, MockService)

        # Now registered
        assert container.has(MockService)

    def test_unregistered_service_error(self):
        """Test error when getting unregistered service."""
        container = DIContainer()

        with pytest.raises(ValueError, match="Service .* not registered"):
            container.get(MockService)


class TestGlobalContainer:
    """Test cases for global container functions."""

    def test_get_container_singleton(self):
        """Test that get_container returns singleton."""
        container1 = get_container()
        container2 = get_container()

        assert container1 is container2

    def test_get_container_returns_di_container(self):
        """Test that get_container returns DIContainer instance."""
        container = get_container()
        assert isinstance(container, DIContainer)
