"""Tests for repositories package modules."""

from __future__ import annotations

from appimage_updater.repositories.base import RepositoryClient, RepositoryError
from appimage_updater.repositories.direct_download_repository import DirectDownloadRepository
from appimage_updater.repositories.dynamic_download_repository import DynamicDownloadRepository
from appimage_updater.repositories.factory import detect_repository_type, get_repository_client
from appimage_updater.repositories.github.repository import GitHubRepository


def test_imports_available() -> None:
    """Test that all expected imports are available from their specific modules."""
    from appimage_updater.repositories.base import RepositoryClient, RepositoryError
    from appimage_updater.repositories.factory import detect_repository_type, get_repository_client

    # All imports should be available
    assert RepositoryClient is not None
    assert RepositoryError is not None
    assert GitHubRepository is not None
    assert DirectDownloadRepository is not None
    assert DynamicDownloadRepository is not None
    assert get_repository_client is not None
    assert detect_repository_type is not None


def test_all_exports() -> None:
    """Test that all expected classes and functions are available from their specific modules."""
    # Since we don't use __all__ in __init__.py files, test direct module imports
    from appimage_updater.repositories.base import RepositoryClient, RepositoryError
    from appimage_updater.repositories.factory import detect_repository_type, get_repository_client

    # Verify all expected classes and functions are importable
    expected_classes = [
        RepositoryClient,
        RepositoryError,
        GitHubRepository,
        DirectDownloadRepository,
        DynamicDownloadRepository,
        get_repository_client,
        detect_repository_type,
    ]

    for item in expected_classes:
        assert item is not None


def test_repository_client_is_abstract() -> None:
    """Test that RepositoryClient is an abstract base class."""

    # Should be a class
    assert isinstance(RepositoryClient, type)

    # Should have abstract methods (can't instantiate directly)
    try:
        RepositoryClient()  # type: ignore[abstract]
        raise AssertionError("Should not be able to instantiate abstract class")
    except TypeError:
        # Expected - abstract class cannot be instantiated
        pass


def test_repository_error_is_exception() -> None:
    """Test that RepositoryError is an exception class."""

    # Should be an exception class
    assert issubclass(RepositoryError, Exception)

    # Should be instantiable
    error = RepositoryError("test error")
    assert str(error) == "test error"


def test_concrete_repository_classes() -> None:
    """Test that concrete repository classes are available."""

    # Should all be classes
    assert isinstance(GitHubRepository, type)
    assert isinstance(DirectDownloadRepository, type)
    assert isinstance(DynamicDownloadRepository, type)


def test_factory_functions() -> None:
    """Test that factory functions are callable."""

    # Should be callable functions
    assert callable(get_repository_client)
    assert callable(detect_repository_type)
