"""Tests for services/__init__.py module."""


def test_imports_available() -> None:
    """Test that all expected imports are available."""
    from appimage_updater.services import (
        ApplicationService,
        CheckService,
        ConfigService,
    )
    
    # All imports should be available
    assert ApplicationService is not None
    assert CheckService is not None
    assert ConfigService is not None


def test_all_exports() -> None:
    """Test that __all__ contains expected exports."""
    from appimage_updater import services
    
    expected_exports = [
        "ApplicationService",
        "CheckService",
        "ConfigService",
    ]
    
    # Check that __all__ is defined and contains expected items
    assert hasattr(services, '__all__')
    assert isinstance(services.__all__, list)
    
    for export in expected_exports:
        assert export in services.__all__


def test_service_classes_are_classes() -> None:
    """Test that all service exports are classes."""
    from appimage_updater.services import (
        ApplicationService,
        CheckService,
        ConfigService,
    )
    
    # Should all be classes
    assert isinstance(ApplicationService, type)
    assert isinstance(CheckService, type)
    assert isinstance(ConfigService, type)


def test_service_classes_instantiable() -> None:
    """Test that service classes can be instantiated."""
    from appimage_updater.services import (
        ApplicationService,
        CheckService,
        ConfigService,
    )
    
    # Should be able to create instances
    app_service = ApplicationService()
    check_service = CheckService()
    config_service = ConfigService()
    
    assert app_service is not None
    assert check_service is not None
    assert config_service is not None


def test_module_docstring() -> None:
    """Test that the module has a proper docstring."""
    from appimage_updater import services
    
    assert services.__doc__ is not None
    assert "Service layer" in services.__doc__
