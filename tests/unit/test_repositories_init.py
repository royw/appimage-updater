"""Tests for repositories/__init__.py module."""


def test_imports_available() -> None:
    """Test that all expected imports are available."""
    from appimage_updater.repositories import (
        DirectDownloadRepository,
        DynamicDownloadRepository,
        GitHubRepository,
        RepositoryClient,
        RepositoryError,
        detect_repository_type,
        get_repository_client,
    )

    # All imports should be available
    assert RepositoryClient is not None
    assert RepositoryError is not None
    assert GitHubRepository is not None
    assert DirectDownloadRepository is not None
    assert DynamicDownloadRepository is not None
    assert get_repository_client is not None
    assert detect_repository_type is not None


def test_all_exports() -> None:
    """Test that __all__ contains expected exports."""
    from appimage_updater import repositories

    expected_exports = [
        "RepositoryClient",
        "RepositoryError",
        "GitHubRepository",
        "DirectDownloadRepository",
        "DynamicDownloadRepository",
        "get_repository_client",
        "detect_repository_type",
    ]

    # Check that __all__ is defined and contains expected items
    assert hasattr(repositories, '__all__')
    assert isinstance(repositories.__all__, list)

    for export in expected_exports:
        assert export in repositories.__all__


def test_repository_client_is_abstract() -> None:
    """Test that RepositoryClient is an abstract base class."""
    from appimage_updater.repositories import RepositoryClient

    # Should be a class
    assert isinstance(RepositoryClient, type)

    # Should have abstract methods (can't instantiate directly)
    try:
        RepositoryClient()  # type: ignore
        assert False, "Should not be able to instantiate abstract class"
    except TypeError:
        # Expected - abstract class cannot be instantiated
        pass


def test_repository_error_is_exception() -> None:
    """Test that RepositoryError is an exception class."""
    from appimage_updater.repositories import RepositoryError

    # Should be an exception class
    assert issubclass(RepositoryError, Exception)

    # Should be instantiable
    error = RepositoryError("test error")
    assert str(error) == "test error"


def test_concrete_repository_classes() -> None:
    """Test that concrete repository classes are available."""
    from appimage_updater.repositories import DirectDownloadRepository, DynamicDownloadRepository, GitHubRepository

    # Should all be classes
    assert isinstance(GitHubRepository, type)
    assert isinstance(DirectDownloadRepository, type)
    assert isinstance(DynamicDownloadRepository, type)


def test_factory_functions() -> None:
    """Test that factory functions are callable."""
    from appimage_updater.repositories import detect_repository_type, get_repository_client

    # Should be callable functions
    assert callable(get_repository_client)
    assert callable(detect_repository_type)
