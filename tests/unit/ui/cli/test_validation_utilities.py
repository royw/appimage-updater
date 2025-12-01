"""Tests for CLI validation utilities warnings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from appimage_updater.ui.cli import validation_utilities as vu


class DummyConsole:
    """Simple console stub to capture printed messages."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def print(self, message: str) -> None:
        self.messages.append(str(message))


class TestCheckHelpers:
    """Tests for individual _check_* helpers."""

    def test_check_rotation_warning_triggers_when_no_symlink(self) -> None:
        warnings: list[str] = []
        app_config: dict[str, Any] = {"rotation": True, "symlink": ""}

        result = vu._check_rotation_warning(app_config, warnings)

        assert result is True
        assert len(warnings) == 1
        assert "Rotation is enabled" in warnings[0]

    def test_check_rotation_warning_ignored_when_rotation_disabled(self) -> None:
        warnings: list[str] = []
        app_config: dict[str, Any] = {"rotation": False}

        result = vu._check_rotation_warning(app_config, warnings)

        assert result is False
        assert warnings == []

    def test_check_download_directory_warning_triggers_for_missing_dir(self, tmp_path: Path) -> None:
        warnings: list[str] = []
        missing_dir = tmp_path / "missing"

        result = vu._check_download_directory_warning(str(missing_dir), warnings)

        assert result is True
        assert len(warnings) == 1
        assert str(missing_dir) in warnings[0]

    def test_check_download_directory_warning_ignored_for_existing_dir(self, tmp_path: Path) -> None:
        warnings: list[str] = []

        result = vu._check_download_directory_warning(str(tmp_path), warnings)

        assert result is False
        assert warnings == []

    def test_check_checksum_warning_triggers_when_disabled(self) -> None:
        warnings: list[str] = []
        app_config: dict[str, Any] = {"checksum": False}

        result = vu._check_checksum_warning(app_config, warnings)

        assert result is True
        assert len(warnings) == 1
        assert "Checksum verification is disabled" in warnings[0]

    def test_check_checksum_warning_ignored_when_enabled_or_default(self) -> None:
        warnings: list[str] = []
        app_config: dict[str, Any] = {}  # defaults to enabled

        result = vu._check_checksum_warning(app_config, warnings)

        assert result is False
        assert warnings == []

    def test_check_pattern_warning_triggers_for_unsafe_pattern(self) -> None:
        warnings: list[str] = []
        app_config: dict[str, Any] = {"pattern": ".*foo"}

        result = vu._check_pattern_warning(app_config, warnings)

        assert result is True
        assert len(warnings) == 1
        assert "contains '.*'" in warnings[0]

    def test_check_pattern_warning_ignored_for_safe_pattern(self) -> None:
        warnings: list[str] = []
        app_config: dict[str, Any] = {"pattern": ".*foo$"}

        result = vu._check_pattern_warning(app_config, warnings)

        assert result is False
        assert warnings == []


class TestDisplayWarnings:
    """Tests for warning display helpers."""

    def test_display_warnings_prints_messages(self, monkeypatch: pytest.MonkeyPatch) -> None:
        dummy_console = DummyConsole()
        monkeypatch.setattr(vu, "console", dummy_console)

        warnings = ["Warning one", "Warning two"]
        vu._display_warnings(warnings)

        # First line is the header, followed by one line per warning
        assert any("Configuration Warnings" in msg for msg in dummy_console.messages)
        assert any("Warning one" in msg for msg in dummy_console.messages)
        assert any("Warning two" in msg for msg in dummy_console.messages)

    def test_display_warnings_prints_nothing_for_empty_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        dummy_console = DummyConsole()
        monkeypatch.setattr(vu, "console", dummy_console)

        vu._display_warnings([])

        assert dummy_console.messages == []

    def test_check_configuration_warnings_integration(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        dummy_console = DummyConsole()
        monkeypatch.setattr(vu, "console", dummy_console)

        # Configure app to trigger multiple warnings
        app_config: dict[str, Any] = {
            "rotation": True,  # triggers rotation warning (no symlink)
            "checksum": False,  # triggers checksum warning
            "pattern": ".*foo",  # triggers pattern warning
        }
        missing_dir = tmp_path / "missing"

        vu._check_configuration_warnings(app_config, str(missing_dir))

        # Expect header plus several warning lines
        assert any("Configuration Warnings" in msg for msg in dummy_console.messages)
        # Spot-check that at least some known phrases are present
        combined = "\n".join(dummy_console.messages)
        assert "Rotation is enabled" in combined
        assert "Checksum verification is disabled" in combined
        assert "contains '.*'" in combined
        assert str(missing_dir) in combined
