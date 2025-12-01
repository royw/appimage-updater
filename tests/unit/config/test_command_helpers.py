"""Unit tests for helper functions in config.command.

These tests focus on the pure-ish helpers and small console-printing helpers
so we can improve coverage without touching the higher-level CLI wiring.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from appimage_updater.config import command as cmd
from appimage_updater.config.command import (
    _apply_checksum_algorithm_setting,
    _apply_concurrent_downloads_setting,
    _apply_retain_count_setting,
    _apply_timeout_setting,
    _build_basic_config_settings,
    _build_checksum_settings,
    _build_default_config_settings,
    _build_main_settings,
    _format_yes_no,
    _apply_setting_change,
    _apply_path_setting,
    _apply_string_setting,
    _apply_rotation_enabled_setting,
    _apply_symlink_enabled_setting,
    _apply_checksum_enabled_setting,
    _apply_checksum_required_setting,
    _apply_prerelease_setting,
    _apply_auto_subdir_setting,
    _print_global_config_rich,
    _print_global_config_structured,
    _print_effective_config_rich,
    _print_effective_config_structured,
    set_global_config_value,
    show_effective_config,
    show_global_config,
    _show_available_settings,
)
from appimage_updater.config.loader import ConfigLoadError
from appimage_updater.config.models import Config


class DummyConsole:
    """Simple console stub to capture printed messages."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def print(self, message: str = "") -> None:
        """Mimic rich.console.Console.print where arguments are optional."""
        self.messages.append(str(message))


class TestFormatAndBuildSettings:
    """Tests for basic formatting and settings-builder helpers."""

    def test_format_yes_no(self) -> None:
        assert _format_yes_no(True) == "Yes"
        assert _format_yes_no(False) == "No"

    def test_build_basic_config_settings(self) -> None:
        global_config = SimpleNamespace(
            concurrent_downloads=3,
            timeout_seconds=30,
            user_agent="MyAgent/1.0",
        )

        settings = _build_basic_config_settings(global_config)

        assert settings["Concurrent Downloads|concurrent-downloads"] == "3"
        assert settings["Timeout Seconds|timeout-seconds"] == "30"
        assert settings["User Agent|user-agent"] == "MyAgent/1.0"

    def test_build_default_config_settings_with_all_values(self) -> None:
        defaults = SimpleNamespace(
            download_dir="/apps",
            symlink_dir="/bin",
            auto_subdir=True,
            rotation_enabled=False,
            retain_count=5,
            symlink_enabled=True,
            symlink_pattern="{name}.AppImage",
            checksum_enabled=True,
            checksum_algorithm="sha256",
            checksum_pattern="{filename}.sha256",
            checksum_required=False,
            prerelease=True,
        )

        settings = _build_default_config_settings(defaults)

        assert settings["Download Directory|download-dir"] == "/apps"
        assert settings["Symlink Directory|symlink-dir"] == "/bin"
        assert settings["Auto Subdirectory|auto-subdir"] == "Yes"
        assert settings["Rotation Enabled|rotation"] == "No"
        assert settings["Retain Count|retain-count"] == "5"
        assert settings["Symlink Enabled|symlink-enabled"] == "Yes"
        assert settings["Symlink Pattern|symlink-pattern"] == "{name}.AppImage"
        assert settings["Checksum Enabled|checksum"] == "Yes"
        assert settings["Checksum Algorithm|checksum-algorithm"] == "SHA256"
        assert settings["Checksum Pattern|checksum-pattern"] == "{filename}.sha256"
        assert settings["Checksum Required|checksum-required"] == "No"
        assert settings["Prerelease|prerelease"] == "Yes"

    def test_build_default_config_settings_with_none_dirs(self) -> None:
        defaults = SimpleNamespace(
            download_dir=None,
            symlink_dir=None,
            auto_subdir=False,
            rotation_enabled=False,
            retain_count=3,
            symlink_enabled=False,
            symlink_pattern="pattern",
            checksum_enabled=False,
            checksum_algorithm="sha1",
            checksum_pattern="{filename}.sha1",
            checksum_required=False,
            prerelease=False,
        )

        settings = _build_default_config_settings(defaults)

        assert settings["Download Directory|download-dir"] == "None (use current directory)"
        assert settings["Symlink Directory|symlink-dir"] == "None"
        assert settings["Auto Subdirectory|auto-subdir"] == "No"

    def test_build_main_settings_with_optional_fields(self) -> None:
        effective = {
            "enabled": True,
            "url": "https://example.com",
            "download_dir": "/apps/MyApp",
            "pattern": "MyApp.*",
            "prerelease": True,
            "auto_subdir": False,
            "rotation_enabled": False,
            "symlink_enabled": True,
            "retain_count": 3,
            "symlink_path": "/apps/MyApp.AppImage",
        }

        settings = _build_main_settings("MyApp", effective)

        assert settings["Application"] == "MyApp"
        assert settings["Enabled"] == "Yes"
        assert settings["URL"] == "https://example.com"
        assert settings["Download Directory"] == "/apps/MyApp"
        assert settings["Pattern"] == "MyApp.*"
        assert settings["Prerelease"] == "Yes"
        assert settings["Auto Subdirectory"] == "No"
        assert settings["Rotation Enabled"] == "No"
        assert settings["Symlink Enabled"] == "Yes"
        # Optional fields present
        assert settings["Retain Count"] == "3"
        assert settings["Symlink Path"] == "/apps/MyApp.AppImage"

    def test_build_main_settings_without_optional_fields(self) -> None:
        effective = {
            "enabled": False,
            "url": "https://example.com",
            "download_dir": "/apps/MyApp",
            "pattern": "MyApp.*",
            "prerelease": False,
            "auto_subdir": False,
            "rotation_enabled": False,
            "symlink_enabled": False,
        }

        settings = _build_main_settings("MyApp", effective)

        assert "Retain Count" not in settings
        assert "Symlink Path" not in settings

    def test_build_checksum_settings_enabled(self) -> None:
        effective = {
            "checksum": {
                "enabled": True,
                "algorithm": "sha256",
                "pattern": "{filename}.sha256",
                "required": True,
            }
        }

        settings = _build_checksum_settings(effective)

        assert settings["Checksum Enabled"] == "Yes"
        assert settings["Checksum Algorithm"] == "SHA256"
        assert settings["Checksum Pattern"] == "{filename}.sha256"
        assert settings["Checksum Required"] == "Yes"

    def test_build_checksum_settings_disabled_or_missing(self) -> None:
        # Disabled: only Enabled key present
        effective_disabled = {"checksum": {"enabled": False}}
        settings_disabled = _build_checksum_settings(effective_disabled)
        assert settings_disabled == {"Checksum Enabled": "No"}

        # Missing checksum entirely
        effective_missing: dict[str, Any] = {}
        settings_missing = _build_checksum_settings(effective_missing)
        assert settings_missing == {}


class TestNumericAndAlgorithmSettings:
    """Tests for numeric and checksum algorithm setting helpers."""

    def test_apply_retain_count_setting_valid_and_invalid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cfg = Config()
        dummy_console = DummyConsole()
        monkeypatch.setattr(cmd, "console", dummy_console)

        # Valid value
        assert _apply_retain_count_setting(cfg, 5) is True
        assert cfg.global_config.defaults.retain_count == 5
        assert any("retain count" in msg for msg in dummy_console.messages)

        # Invalid value
        dummy_console.messages.clear()
        assert _apply_retain_count_setting(cfg, 0) is False
        assert any("Retain count must be between 1 and 10" in msg for msg in dummy_console.messages)

    def test_apply_concurrent_downloads_setting_valid_and_invalid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cfg = Config()
        dummy_console = DummyConsole()
        monkeypatch.setattr(cmd, "console", dummy_console)

        # Valid
        assert _apply_concurrent_downloads_setting(cfg, 4) is True
        assert cfg.global_config.concurrent_downloads == 4
        assert any("concurrent downloads" in msg.lower() for msg in dummy_console.messages)

        # Invalid
        dummy_console.messages.clear()
        assert _apply_concurrent_downloads_setting(cfg, 0) is False
        assert any("Concurrent downloads must be between 1 and 10" in msg for msg in dummy_console.messages)

    def test_apply_timeout_setting_valid_and_invalid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cfg = Config()
        dummy_console = DummyConsole()
        monkeypatch.setattr(cmd, "console", dummy_console)

        # Valid
        assert _apply_timeout_setting(cfg, 10) is True
        assert cfg.global_config.timeout_seconds == 10
        assert any("Set timeout" in msg for msg in dummy_console.messages)

        # Invalid
        dummy_console.messages.clear()
        assert _apply_timeout_setting(cfg, 1) is False
        assert any("Timeout must be between 5 and 300 seconds" in msg for msg in dummy_console.messages)

    def test_apply_checksum_algorithm_setting_valid_and_invalid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        dummy_console = DummyConsole()
        monkeypatch.setattr(cmd, "console", dummy_console)

        # Valid algorithms - use separate Config instances to avoid mypy literal narrowing issues
        cfg_sha256 = Config()
        assert _apply_checksum_algorithm_setting(cfg_sha256, "sha256") is True
        assert cfg_sha256.global_config.defaults.checksum_algorithm == "sha256"

        cfg_sha1 = Config()
        assert _apply_checksum_algorithm_setting(cfg_sha1, "SHA1") is True
        assert cfg_sha1.global_config.defaults.checksum_algorithm == "sha1"

        cfg_md5 = Config()
        assert _apply_checksum_algorithm_setting(cfg_md5, "md5") is True
        assert cfg_md5.global_config.defaults.checksum_algorithm == "md5"

        # Invalid algorithm
        dummy_console.messages.clear()
        cfg_invalid = Config()
        assert _apply_checksum_algorithm_setting(cfg_invalid, "foo") is False
        assert any("Checksum algorithm must be one of" in msg for msg in dummy_console.messages)

    def test_apply_setting_change_checksum_algorithm_special_case(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """_apply_setting_change should delegate checksum-algorithm to the special-case helper."""

        cfg = Config()
        dummy_console = DummyConsole()
        monkeypatch.setattr(cmd, "console", dummy_console)

        result = _apply_setting_change(cfg, "checksum-algorithm", "sha256")

        assert result is True
        assert cfg.global_config.defaults.checksum_algorithm == "sha256"

    def test_apply_setting_change_unknown_setting_calls_show_available_settings(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Unknown settings should cause _apply_setting_change to return False and emit help text."""

        cfg = Config()
        dummy_console = DummyConsole()
        monkeypatch.setattr(cmd, "console", dummy_console)

        result = _show_available_settings("unknown-setting")

        assert result is False
        combined = "\n".join(dummy_console.messages)
        assert "Unknown setting: unknown-setting" in combined
        assert "Available settings" in combined
        assert "download-dir" in combined
        assert "process-pool-size" in combined


class TestApplyHelpersWithInjectedConsole:
    """Tests for _apply_* helpers that now accept an injected console."""

    def test_apply_path_setting_uses_injected_console(self) -> None:
        cfg = Config()
        dummy_console = DummyConsole()

        _apply_path_setting(cfg, "download-dir", "/apps", console_to_use=dummy_console)

        assert cfg.global_config.defaults.download_dir == Path("/apps")
        combined = "\n".join(dummy_console.messages)
        assert "Set default download directory to: /apps" in combined

    def test_apply_string_setting_uses_injected_console(self) -> None:
        cfg = Config()
        dummy_console = DummyConsole()

        _apply_string_setting(cfg, "symlink-pattern", "{name}.AppImage", console_to_use=dummy_console)

        assert cfg.global_config.defaults.symlink_pattern == "{name}.AppImage"
        combined = "\n".join(dummy_console.messages)
        assert "Set default symlink pattern to: {name}.AppImage" in combined

    def test_apply_boolean_helpers_use_injected_console(self) -> None:
        cfg = Config()
        dummy_console = DummyConsole()

        _apply_rotation_enabled_setting(cfg, True, console_to_use=dummy_console)
        _apply_symlink_enabled_setting(cfg, True, console_to_use=dummy_console)
        _apply_checksum_enabled_setting(cfg, True, console_to_use=dummy_console)
        _apply_checksum_required_setting(cfg, False, console_to_use=dummy_console)
        _apply_prerelease_setting(cfg, True, console_to_use=dummy_console)
        _apply_auto_subdir_setting(cfg, True, console_to_use=dummy_console)

        assert cfg.global_config.defaults.rotation_enabled is True
        assert cfg.global_config.defaults.symlink_enabled is True
        assert cfg.global_config.defaults.checksum_enabled is True
        assert cfg.global_config.defaults.checksum_required is False
        assert cfg.global_config.defaults.prerelease is True
        assert cfg.global_config.defaults.auto_subdir is True

        combined = "\n".join(dummy_console.messages)
        assert "Set default rotation enabled to: True" in combined
        assert "Set default symlink enabled to: True" in combined
        assert "Set default checksum enabled to: True" in combined
        assert "Set default checksum required to: False" in combined
        assert "Set default prerelease to: True" in combined
        assert "Set automatic subdirectory creation to: True" in combined


class TestHandleConfigLoadError:
    """Tests for _handle_config_load_error with injected console."""

    def test_handle_config_load_error_uses_injected_console(self) -> None:
        dummy_console = DummyConsole()
        error = ConfigLoadError("failed to load config")

        result = cmd._handle_config_load_error(error, err_console=dummy_console)

        assert result is False
        combined = "\n".join(dummy_console.messages)
        assert "Error loading configuration" in combined
        assert "failed to load config" in combined
        assert "Run 'appimage-updater init'" in combined


class TestGlobalConfigPrinting:
    """Tests for global config printing helpers that use output_formatter injection."""

    def _make_sample_global_and_defaults(self) -> tuple[Any, Any]:
        """Create simple global_config and defaults objects for printing tests."""
        global_config = SimpleNamespace(
            concurrent_downloads=2,
            timeout_seconds=60,
            user_agent="TestAgent/1.0",
            defaults=None,  # unused here
        )

        defaults = SimpleNamespace(
            download_dir="/apps",
            symlink_dir="/bin",
            auto_subdir=True,
            rotation_enabled=True,
            retain_count=3,
            symlink_enabled=True,
            symlink_pattern="{name}.AppImage",
            checksum_enabled=True,
            checksum_algorithm="sha256",
            checksum_pattern="{filename}.sha256",
            checksum_required=False,
            prerelease=False,
        )

        return global_config, defaults

    def test_print_global_config_structured_uses_formatter(self) -> None:
        """_print_global_config_structured should call formatter.print_config_settings with merged settings."""

        class StubFormatter:
            def __init__(self) -> None:
                self.received_settings: dict[str, str] | None = None

            def print_config_settings(self, settings: dict[str, str]) -> None:
                self.received_settings = settings

        formatter = StubFormatter()
        global_config, defaults = self._make_sample_global_and_defaults()

        _print_global_config_structured(global_config, defaults, formatter)

        assert formatter.received_settings is not None
        # Spot-check a few keys from both basic and default settings
        settings = formatter.received_settings
        assert "Concurrent Downloads|concurrent-downloads" in settings
        assert "Download Directory|download-dir" in settings

    def test_print_global_config_rich_uses_formatter_console(self) -> None:
        """_print_global_config_rich should use the formatter's console when available."""

        class FormatterWithConsole:
            def __init__(self, console: DummyConsole) -> None:
                self.console = console

        dummy_console = DummyConsole()
        formatter = FormatterWithConsole(dummy_console)
        global_config, defaults = self._make_sample_global_and_defaults()

        _print_global_config_rich(global_config, defaults, formatter)

        combined = "\n".join(dummy_console.messages)
        # Header and section titles should be present (Rich markup stripped for comparison by substring only)
        assert "Global Configuration" in combined
        assert "Basic Settings:" in combined
        assert "Default Settings for New Applications:" in combined

    def test_show_global_config_with_injected_factories_structured_path(self) -> None:
        """show_global_config should use structured printing when formatter has no console."""

        class StubDefaults(SimpleNamespace):
            pass

        class StubGlobalConfig(SimpleNamespace):
            pass

        class StubConfig(SimpleNamespace):
            pass

        class StubAppConfigs:
            def __init__(self, _path: Path | None) -> None:
                defaults = StubDefaults(
                    download_dir="/apps",
                    symlink_dir=None,
                    auto_subdir=True,
                    rotation_enabled=False,
                    retain_count=3,
                    symlink_enabled=False,
                    symlink_pattern="{name}.AppImage",
                    checksum_enabled=True,
                    checksum_algorithm="sha256",
                    checksum_pattern="{filename}.sha256",
                    checksum_required=False,
                    prerelease=False,
                )
                global_config = StubGlobalConfig(
                    concurrent_downloads=2,
                    timeout_seconds=30,
                    user_agent="UA/1.0",
                    defaults=defaults,
                )
                self._config = StubConfig(global_config=global_config)

        class CapturingFormatter:
            def __init__(self) -> None:
                self.received_settings: dict[str, str] | None = None

            def print_config_settings(self, settings: dict[str, str]) -> None:
                self.received_settings = settings

        formatter = CapturingFormatter()

        # Call show_global_config with injected factories; config_file/dir are irrelevant for StubAppConfigs
        show_global_config(
            config_file=None,
            config_dir=Path("/unused"),
            app_configs_factory=lambda p: StubAppConfigs(p),
            formatter_factory=lambda: formatter,
        )

        assert formatter.received_settings is not None
        assert "Concurrent Downloads|concurrent-downloads" in formatter.received_settings


class TestEffectiveConfigPrinting:
    """Tests for effective config printing helpers that use output_formatter/console."""

    def _make_sample_effective_config(self) -> dict[str, Any]:
        """Create a simple effective_config dict for tests."""
        return {
            "name": "MyApp",
            "source_type": "github",
            "url": "https://example.com/MyApp",
            "download_dir": "/apps/MyApp",
            "pattern": "MyApp.*",
            "enabled": True,
            "prerelease": False,
            "rotation_enabled": False,
            "auto_subdir": True,
            "retain_count": 3,
            "symlink_path": "/apps/MyApp.AppImage",
            "checksum": {
                "enabled": True,
                "algorithm": "sha256",
                "pattern": "{filename}.sha256",
                "required": False,
            },
        }

    def test_print_effective_config_structured_uses_formatter(self) -> None:
        """_print_effective_config_structured should call formatter.print_config_settings."""

        class StubFormatter:
            def __init__(self) -> None:
                self.received_settings: dict[str, str] | None = None

            def print_config_settings(self, settings: dict[str, str]) -> None:
                self.received_settings = settings

        formatter = StubFormatter()
        effective_config = self._make_sample_effective_config()

        _print_effective_config_structured("MyApp", effective_config, formatter)

        assert formatter.received_settings is not None
        settings = formatter.received_settings
        # Spot-check a few keys
        assert settings["Application"] == "MyApp"
        assert settings["URL"] == "https://example.com/MyApp"
        assert settings["Checksum Enabled"] == "Yes"

    def test_print_effective_config_rich_uses_formatter_console(self) -> None:
        """_print_effective_config_rich should use the formatter's console when available."""

        class FormatterWithConsole:
            def __init__(self, console: DummyConsole) -> None:
                self.console = console

        dummy_console = DummyConsole()
        formatter = FormatterWithConsole(dummy_console)
        effective_config = self._make_sample_effective_config()

        _print_effective_config_rich("MyApp", effective_config, formatter)

        combined = "\n".join(dummy_console.messages)
        # Header and section titles should be present
        assert "Effective Configuration for 'MyApp'" in combined
        assert "Checksum Settings:" in combined

    def test_show_effective_config_structured_with_injected_factories(self) -> None:
        """show_effective_config should use structured printing when formatter has no console."""

        class StubAppConfigs:
            def __init__(self, _path: Path | None) -> None:
                effective_config = TestEffectiveConfigPrinting()._make_sample_effective_config()

                class StubConfig(SimpleNamespace):
                    pass

                # Store a config object whose get_effective_config_for_app returns the sample dict
                self._config = StubConfig(
                    get_effective_config_for_app=lambda _name: effective_config,
                )

        class CapturingFormatter:
            def __init__(self) -> None:
                self.received_settings: dict[str, str] | None = None

            def print_config_settings(self, settings: dict[str, str]) -> None:
                self.received_settings = settings

        formatter = CapturingFormatter()

        show_effective_config(
            app_name="MyApp",
            config_file=None,
            config_dir=Path("/unused"),
            app_configs_factory=lambda p: StubAppConfigs(p),
            formatter_factory=lambda: formatter,
        )

        assert formatter.received_settings is not None
        settings = formatter.received_settings
        assert settings["Application"] == "MyApp"

    def test_show_effective_config_app_not_found_uses_handle_app_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """show_effective_config should call _handle_app_not_found when config is missing."""

        class StubConfig(SimpleNamespace):
            pass

        class StubAppConfigs:
            def __init__(self, _path: Path | None) -> None:
                self._config = StubConfig(
                    get_effective_config_for_app=lambda _name: None,
                )

        dummy_console = DummyConsole()
        monkeypatch.setattr(cmd, "console", dummy_console)

        show_effective_config(
            app_name="MissingApp",
            config_file=None,
            config_dir=Path("/unused"),
            app_configs_factory=lambda p: StubAppConfigs(p),
            formatter_factory=lambda: object(),  # Not used when app is missing
        )

        combined = "\n".join(dummy_console.messages)
        assert "Application 'MissingApp' not found in configuration." in combined


class TestSetGlobalConfigValue:
    """Tests for set_global_config_value using an injected GlobalConfigManager stub."""

    def test_set_global_config_value_updates_in_memory_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class StubManager:
            def __init__(self, _path: Path | None) -> None:
                self.config = Config()

        # Prevent actual filesystem writes from _save_config
        monkeypatch.setattr(cmd, "_save_config", lambda *args, **kwargs: None)

        stub_manager = StubManager(None)

        # Use a lambda that returns our pre-created stub so we can assert on it afterwards
        result = set_global_config_value(
            setting="retain-count",
            value="5",
            config_file=None,
            config_dir=None,
            global_manager_factory=lambda p: stub_manager,
        )

        assert result is True
        # Verify the numeric setting was applied to the in-memory config
        assert stub_manager.config.global_config.defaults.retain_count == 5


class TestHandleAppNotFound:
    """Tests for _handle_app_not_found using DummyConsole via monkeypatch."""

    def test_handle_app_not_found_uses_module_console(self, monkeypatch: pytest.MonkeyPatch) -> None:
        dummy_console = DummyConsole()
        monkeypatch.setattr(cmd, "console", dummy_console)

        result = cmd._handle_app_not_found("MissingApp")

        assert result is False
        combined = "\n".join(dummy_console.messages)
        assert "Application 'MissingApp' not found in configuration." in combined
