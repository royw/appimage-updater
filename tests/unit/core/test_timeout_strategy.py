"""Tests for timeout strategy module."""

from __future__ import annotations

from appimage_updater.core.timeout_strategy import (
    ProgressiveTimeoutClient,
    TimeoutStrategy,
    create_progressive_client,
    get_default_timeout_strategy,
)


class TestTimeoutStrategy:
    """Tests for TimeoutStrategy class."""

    def test_initialization_default(self) -> None:
        """Test default initialization."""
        strategy = TimeoutStrategy()

        assert strategy.base_timeout == 30
        assert "quick_check" in strategy.timeouts
        assert "page_scraping" in strategy.timeouts
        assert "api_request" in strategy.timeouts
        assert "download" in strategy.timeouts
        assert "fallback" in strategy.timeouts

    def test_initialization_custom_timeout(self) -> None:
        """Test initialization with custom base timeout."""
        strategy = TimeoutStrategy(base_timeout=60)

        assert strategy.base_timeout == 60
        assert strategy.timeouts["download"] == 600  # 60 * 10

    def test_timeout_values(self) -> None:
        """Test timeout values are set correctly."""
        strategy = TimeoutStrategy(base_timeout=30)

        assert strategy.timeouts["quick_check"] == 5
        assert strategy.timeouts["page_scraping"] == 10
        assert strategy.timeouts["api_request"] == 15
        assert strategy.timeouts["download"] == 300  # 30 * 10
        assert strategy.timeouts["fallback"] == 30

    def test_get_timeout_quick_check(self) -> None:
        """Test getting quick_check timeout."""
        strategy = TimeoutStrategy()

        timeout = strategy.get_timeout("quick_check")

        assert timeout == 5

    def test_get_timeout_page_scraping(self) -> None:
        """Test getting page_scraping timeout."""
        strategy = TimeoutStrategy()

        timeout = strategy.get_timeout("page_scraping")

        assert timeout == 10

    def test_get_timeout_api_request(self) -> None:
        """Test getting api_request timeout."""
        strategy = TimeoutStrategy()

        timeout = strategy.get_timeout("api_request")

        assert timeout == 15

    def test_get_timeout_download(self) -> None:
        """Test getting download timeout."""
        strategy = TimeoutStrategy(base_timeout=30)

        timeout = strategy.get_timeout("download")

        assert timeout == 300

    def test_get_timeout_fallback(self) -> None:
        """Test getting fallback timeout."""
        strategy = TimeoutStrategy()

        timeout = strategy.get_timeout("fallback")

        assert timeout == 30

    def test_get_timeout_unknown_type(self) -> None:
        """Test getting timeout for unknown type returns fallback."""
        strategy = TimeoutStrategy()

        timeout = strategy.get_timeout("unknown_type")

        assert timeout == 30  # fallback

    def test_get_timeout_default_parameter(self) -> None:
        """Test get_timeout with default parameter."""
        strategy = TimeoutStrategy()

        timeout = strategy.get_timeout()

        assert timeout == 30  # fallback

    def test_create_client_config_basic(self) -> None:
        """Test creating basic client config."""
        strategy = TimeoutStrategy()

        config = strategy.create_client_config("api_request")

        assert config["timeout"] == 15
        assert len(config) == 1

    def test_create_client_config_with_kwargs(self) -> None:
        """Test creating client config with additional kwargs."""
        strategy = TimeoutStrategy()

        config = strategy.create_client_config("download", follow_redirects=True, max_redirects=10)

        assert config["timeout"] == 300
        assert config["follow_redirects"] is True
        assert config["max_redirects"] == 10

    def test_create_client_config_default_operation(self) -> None:
        """Test creating client config with default operation type."""
        strategy = TimeoutStrategy()

        config = strategy.create_client_config()

        assert config["timeout"] == 30  # fallback


class TestProgressiveTimeoutClient:
    """Tests for ProgressiveTimeoutClient class."""

    def test_initialization(self) -> None:
        """Test client initialization."""
        strategy = TimeoutStrategy()
        client = ProgressiveTimeoutClient(strategy)

        assert client.timeout_strategy == strategy

    def test_prepare_operation_types_default(self) -> None:
        """Test preparing operation types with None."""
        strategy = TimeoutStrategy()
        client = ProgressiveTimeoutClient(strategy)

        types = client._prepare_operation_types(None)

        assert types == ["quick_check", "fallback"]

    def test_prepare_operation_types_custom(self) -> None:
        """Test preparing operation types with custom list."""
        strategy = TimeoutStrategy()
        client = ProgressiveTimeoutClient(strategy)

        custom_types = ["api_request", "download"]
        types = client._prepare_operation_types(custom_types)

        assert types == custom_types


class TestGlobalFunctions:
    """Tests for global timeout strategy functions."""

    def test_get_default_timeout_strategy_first_call(self) -> None:
        """Test getting default timeout strategy for first time."""
        # Clear the global
        import appimage_updater.core.timeout_strategy as module

        module._default_timeout_strategy = None

        strategy = get_default_timeout_strategy()

        assert isinstance(strategy, TimeoutStrategy)
        assert strategy.base_timeout == 30

    def test_get_default_timeout_strategy_cached(self) -> None:
        """Test that default timeout strategy is cached."""
        # Clear the global
        import appimage_updater.core.timeout_strategy as module

        module._default_timeout_strategy = None

        strategy1 = get_default_timeout_strategy()
        strategy2 = get_default_timeout_strategy()

        assert strategy1 is strategy2

    def test_get_default_timeout_strategy_custom_timeout(self) -> None:
        """Test getting default strategy with custom timeout."""
        # Clear the global
        import appimage_updater.core.timeout_strategy as module

        module._default_timeout_strategy = None

        strategy = get_default_timeout_strategy(base_timeout=60)

        assert strategy.base_timeout == 60

    def test_get_default_timeout_strategy_recreates_on_different_timeout(self) -> None:
        """Test that strategy is recreated when base_timeout changes."""
        # Clear the global
        import appimage_updater.core.timeout_strategy as module

        module._default_timeout_strategy = None

        strategy1 = get_default_timeout_strategy(base_timeout=30)
        strategy2 = get_default_timeout_strategy(base_timeout=60)

        assert strategy1 is not strategy2
        assert strategy2.base_timeout == 60

    def test_create_progressive_client_default(self) -> None:
        """Test creating progressive client with default timeout."""
        client = create_progressive_client()

        assert isinstance(client, ProgressiveTimeoutClient)
        assert isinstance(client.timeout_strategy, TimeoutStrategy)
        assert client.timeout_strategy.base_timeout == 30

    def test_create_progressive_client_custom_timeout(self) -> None:
        """Test creating progressive client with custom timeout."""
        client = create_progressive_client(base_timeout=60)

        assert isinstance(client, ProgressiveTimeoutClient)
        assert client.timeout_strategy.base_timeout == 60


class TestIntegrationScenarios:
    """Integration tests for timeout strategy usage."""

    def test_complete_timeout_strategy_workflow(self) -> None:
        """Test complete workflow from strategy creation to config."""
        strategy = TimeoutStrategy(base_timeout=45)

        # Get different timeouts
        quick = strategy.get_timeout("quick_check")
        api = strategy.get_timeout("api_request")
        download = strategy.get_timeout("download")

        assert quick < api < download
        assert download == 450  # 45 * 10

    def test_progressive_client_creation_workflow(self) -> None:
        """Test creating and using progressive client."""
        client = create_progressive_client(base_timeout=30)

        assert client.timeout_strategy.base_timeout == 30
        assert client.timeout_strategy.get_timeout("quick_check") == 5

    def test_timeout_configuration_consistency(self) -> None:
        """Test that timeout configuration is consistent."""
        strategy1 = TimeoutStrategy(base_timeout=30)
        strategy2 = TimeoutStrategy(base_timeout=30)

        # Both should have same timeout values
        for key in strategy1.timeouts:
            assert strategy1.timeouts[key] == strategy2.timeouts[key]
