"""Unit tests for config operations functions, including --force functionality."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

import pytest

from appimage_updater.config.operations import (
    _get_effective_checksum_config,
    _get_effective_download_dir,
    _validate_direct_url,
    collect_checksum_edit_updates,
    collect_edit_updates,
    collect_rotation_edit_updates,
    validate_basic_field_updates,
    validate_add_rotation_config,
    validate_symlink_path,
    validate_symlink_path_characters,
    validate_symlink_path_exists,
    validate_url_update,
)


class TestCollectEditUpdates:
    """Test the collect_edit_updates function."""

    def test_collect_edit_updates_passes_force_to_basic(self) -> None:
        """Test that collect_edit_updates passes force parameter to basic updates."""
        updates = collect_edit_updates(
            url="https://example.com/app.AppImage",
            download_dir=None,
            basename=None,
            pattern=None,
            enable=None,
            prerelease=None,
            rotation=None,
            symlink_path=None,
            retain_count=None,
            checksum=None,
            checksum_algorithm=None,
            checksum_pattern=None,
            checksum_required=None,
            force=True,
        )

        assert "url" in updates
        assert "force" in updates
        assert updates["force"] is True

    def test_collect_edit_updates_force_default_false(self) -> None:
        """Test that force defaults to False in collect_edit_updates."""
        updates = collect_edit_updates(
            url="https://github.com/test/repo",
            download_dir=None,
            basename=None,
            pattern=None,
            enable=None,
            prerelease=None,
            rotation=None,
            symlink_path=None,
            retain_count=None,
            checksum=None,
            checksum_algorithm=None,
            checksum_pattern=None,
            checksum_required=None,
        )

        assert "url" in updates
        assert "force" in updates
        assert updates["force"] is False


class TestValidateUrlUpdate:
    """Test the validate_url_update function."""

    @patch("appimage_updater.config.operations.console")
    @patch("appimage_updater.config.operations.logger")
    def test_validate_url_update_with_force_skips_validation(self, mock_logger: Mock, mock_console: Mock) -> None:
        """Test that validate_url_update skips validation when force=True."""
        updates = {
            "url": "https://direct-download.com/app.AppImage",
            "force": True,
        }

        # Should not raise any exception
        validate_url_update(updates)

        # Should print warning message
        mock_console.print.assert_called_once_with(
            "[yellow]Warning: Using --force: Skipping URL validation and normalization"
        )

        # Should log debug message
        mock_logger.debug.assert_called_once_with(
            "Skipping URL validation for 'https://direct-download.com/app.AppImage' due to --force flag"
        )

        # Force flag should be removed from updates
        assert "force" not in updates
        assert updates["url"] == "https://direct-download.com/app.AppImage"

    @patch("appimage_updater.config.operations.get_repository_client")
    def test_validate_url_update_without_force_performs_validation(self, mock_get_client: Mock) -> None:
        """Test that validate_url_update performs normal validation when force=False."""
        mock_client = MagicMock()
        mock_client.normalize_repo_url.return_value = ("https://github.com/owner/repo", True)
        mock_get_client.return_value = mock_client

        updates = {
            "url": "https://github.com/owner/repo/releases/download/v1.0/app.AppImage",
            "force": False,
        }

        validate_url_update(updates)

        # Should call repository client methods
        mock_get_client.assert_called_once_with("https://github.com/owner/repo/releases/download/v1.0/app.AppImage")
        mock_client.normalize_repo_url.assert_called_once()
        mock_client.parse_repo_url.assert_called_once_with("https://github.com/owner/repo")

        # URL should be normalized
        assert updates["url"] == "https://github.com/owner/repo"

    def test_validate_url_update_no_url_returns_early(self, tmp_path: Path) -> None:
        """Test that validate_url_update returns early when no URL is provided."""
        updates = {"download_dir": str(tmp_path / "test")}

        # Should not raise any exception
        validate_url_update(updates)

        # Updates should remain unchanged
        assert updates == {"download_dir": str(tmp_path / "test")}

    @patch("appimage_updater.config.operations.console")
    @patch("appimage_updater.config.operations.logger")
    def test_validate_url_update_force_removes_flag_from_updates(self, mock_logger: Mock, mock_console: Mock) -> None:
        """Test that force flag is removed from updates after processing."""
        updates = {
            "url": "https://example.com/app.AppImage",
            "force": True,
            "other_field": "value",
        }

        validate_url_update(updates)

        # Force flag should be removed
        assert "force" not in updates
        # Other fields should remain
        assert updates["url"] == "https://example.com/app.AppImage"
        assert updates["other_field"] == "value"

    @patch("appimage_updater.config.operations.get_repository_client")
    def test_validate_url_update_without_force_flag_performs_validation(self, mock_get_client: Mock) -> None:
        """Test validation when force flag is not present (defaults to False)."""
        mock_client = MagicMock()
        mock_client.normalize_repo_url.return_value = ("https://github.com/test/repo", False)
        mock_get_client.return_value = mock_client

        updates = {
            "url": "https://github.com/test/repo",
        }

        validate_url_update(updates)

        # Should perform validation
        mock_get_client.assert_called_once_with("https://github.com/test/repo")
        mock_client.normalize_repo_url.assert_called_once()

    @patch("appimage_updater.config.operations.get_repository_client")
    def test_validate_url_update_validation_error_propagates(self, mock_get_client: Mock) -> None:
        """Test that validation errors are properly propagated when not using force."""
        mock_client = MagicMock()
        mock_client.normalize_repo_url.side_effect = ValueError("Invalid URL")
        mock_get_client.return_value = mock_client

        updates = {
            "url": "https://invalid-url.com",
            "force": False,
        }

        with pytest.raises(ValueError, match="Invalid repository URL"):
            validate_url_update(updates)

    @patch("appimage_updater.config.operations.console")
    @patch("appimage_updater.config.operations.logger")
    def test_validate_url_update_force_bypasses_validation_errors(self, mock_logger: Mock, mock_console: Mock) -> None:
        """Test that force flag bypasses validation errors completely."""
        updates = {
            "url": "https://completely-invalid-url-that-would-fail-validation",
            "force": True,
        }

        # Should not raise any exception even with invalid URL
        validate_url_update(updates)

        # Should show force message
        mock_console.print.assert_called_once()
        mock_logger.debug.assert_called_once()

        # URL should be preserved exactly as provided
        assert updates["url"] == "https://completely-invalid-url-that-would-fail-validation"
        assert "force" not in updates


class TestValidateAddRotationConfig:
    """Tests for validate_add_rotation_config helper."""

    @patch("appimage_updater.config.operations.console")
    def test_rotation_true_without_symlink_shows_error_and_returns_false(self, mock_console: Mock) -> None:
        """--rotation without symlink should be rejected with helpful messaging."""
        result = validate_add_rotation_config(rotation=True, symlink=None)

        assert result is False
        # At least one error message should be printed mentioning --rotation
        calls = "".join(str(call) for call in mock_console.print.call_args_list)
        assert "--rotation requires a symlink path" in calls

    @patch("appimage_updater.config.operations.console")
    def test_rotation_none_or_false_is_allowed(self, mock_console: Mock) -> None:
        """Rotation disabled or unspecified should pass validation."""
        assert validate_add_rotation_config(rotation=False, symlink=None) is True
        assert validate_add_rotation_config(rotation=None, symlink=None) is True

        # No error message should be printed for valid combinations
        assert mock_console.print.call_count == 0


class TestGetEffectiveDownloadDir:
    """Tests for _get_effective_download_dir helper."""

    def test_explicit_download_dir_is_used_as_is(self) -> None:
        """If download_dir is provided, it should be returned unchanged."""
        result = _get_effective_download_dir("/custom/path", defaults=None, name="App")
        assert result == "/custom/path"

    def test_defaults_used_when_no_download_dir(self) -> None:
        """When no download_dir is given, use defaults.get_default_download_dir(name)."""
        defaults = SimpleNamespace(get_default_download_dir=lambda name: Path(f"/defaults/{name}"))

        result = _get_effective_download_dir(None, defaults=defaults, name="MyApp")
        assert result == "/defaults/MyApp"

    def test_current_working_directory_used_when_no_defaults(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without download_dir or defaults, use Path.cwd() / name."""
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

        result = _get_effective_download_dir(None, defaults=None, name="TestApp")
        assert result == str(tmp_path / "TestApp")


class TestGetEffectiveChecksumConfig:
    """Tests for _get_effective_checksum_config and its helpers."""

    def test_defaults_when_all_values_none_and_no_defaults(self) -> None:
        """Without explicit values or defaults, built-in checksum defaults are used."""
        config = _get_effective_checksum_config(
            checksum=None,
            checksum_algorithm=None,
            checksum_pattern=None,
            checksum_required=None,
            defaults=None,
        )

        assert config == {
            "enabled": True,
            "algorithm": "sha256",
            "pattern": "{filename}-SHA256.txt",
            "required": False,
        }

    def test_explicit_values_override_defaults(self) -> None:
        """Explicit checksum parameters should override defaults when provided."""
        defaults = SimpleNamespace(
            checksum_enabled=False,
            checksum_algorithm="md5",
            checksum_pattern="{filename}.md5",
            checksum_required=True,
        )

        config = _get_effective_checksum_config(
            checksum=True,
            checksum_algorithm="sha1",
            checksum_pattern="{filename}.sha1",
            checksum_required=False,
            defaults=defaults,
        )

        assert config == {
            "enabled": True,
            "algorithm": "sha1",
            "pattern": "{filename}.sha1",
            "required": False,
        }


class TestCollectEditUpdateHelpers:
    """Tests for simple edit-update collector helpers."""

    def test_collect_rotation_edit_updates_includes_only_provided_fields(self) -> None:
        """collect_rotation_edit_updates should only include non-None fields."""
        updates = collect_rotation_edit_updates(rotation=True, symlink_path="/tmp/link", retain_count=None)
        assert updates == {"rotation_enabled": True, "symlink_path": "/tmp/link"}

        updates_empty = collect_rotation_edit_updates(rotation=None, symlink_path=None, retain_count=None)
        assert updates_empty == {}

    def test_collect_checksum_edit_updates_includes_only_provided_fields(self) -> None:
        """collect_checksum_edit_updates should only include non-None fields."""
        updates = collect_checksum_edit_updates(
            checksum=True,
            checksum_algorithm="sha256",
            checksum_pattern="{filename}.sha256",
            checksum_required=None,
        )
        assert updates == {
            "checksum_enabled": True,
            "checksum_algorithm": "sha256",
            "checksum_pattern": "{filename}.sha256",
        }

        updates_empty = collect_checksum_edit_updates(None, None, None, None)
        assert updates_empty == {}


class TestSymlinkPathValidators:
    """Tests for basic symlink path validation helpers."""

    def test_validate_symlink_path_exists_rejects_empty_or_whitespace(self) -> None:
        """Empty or whitespace-only symlink paths should raise ValueError."""
        with pytest.raises(ValueError, match="Symlink path cannot be empty"):
            validate_symlink_path_exists("")

        with pytest.raises(ValueError, match="Symlink path cannot be empty"):
            validate_symlink_path_exists("   ")

    def test_validate_symlink_path_exists_allows_non_empty(self) -> None:
        """Non-empty paths should pass existence check."""
        validate_symlink_path_exists("/tmp/app.AppImage")

    def test_validate_symlink_path_characters_rejects_invalid_chars(self, tmp_path: Path) -> None:
        """Paths containing NUL or newline characters should be rejected."""
        bad_path = tmp_path / "bad\nname.AppImage"

        with pytest.raises(ValueError, match="invalid characters"):
            validate_symlink_path_characters(bad_path, str(bad_path))

    def test_validate_symlink_path_characters_accepts_normal_paths(self, tmp_path: Path) -> None:
        """Regular filesystem paths should be accepted."""
        good_path = tmp_path / "good.AppImage"
        # Should not raise
        validate_symlink_path_characters(good_path, str(good_path))

    def test_validate_symlink_path_updates_to_normalized_absolute(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """validate_symlink_path should normalize and store an absolute .AppImage path."""
        # Use a path under tmp_path to avoid relying on the real CWD structure
        raw_path = tmp_path / "subdir" / "MyApp.AppImage"
        updates = {"symlink_path": str(raw_path)}

        validate_symlink_path(updates)

        # Path should now be absolute and still end with the same relative segments
        normalized = updates["symlink_path"]
        assert Path(normalized).is_absolute()
        assert normalized.endswith("subdir/MyApp.AppImage")

    def test_validate_symlink_path_rejects_non_appimage_extension(self, tmp_path: Path) -> None:
        """Non-.AppImage symlink paths should be rejected by the full validator."""
        raw_path = tmp_path / "subdir" / "MyApp.txt"
        updates = {"symlink_path": str(raw_path)}

        with pytest.raises(ValueError, match=r"\.AppImage"):
            validate_symlink_path(updates)

    def test_validate_symlink_path_noop_when_missing_key(self) -> None:
        """If 'symlink_path' is not present, validate_symlink_path should be a no-op."""
        updates: dict[str, str] = {}
        validate_symlink_path(updates)
        assert updates == {}


class TestValidateDirectUrl:
    """Tests for the _validate_direct_url helper used by validate_and_normalize_add_url."""

    def test_validate_direct_url_accepts_well_formed_url(self) -> None:
        """A well-formed URL with scheme and host should be returned unchanged."""
        result = _validate_direct_url("https://example.com/app.AppImage")
        assert result == "https://example.com/app.AppImage"

    @patch("appimage_updater.config.operations.console")
    def test_validate_direct_url_rejects_missing_scheme_or_host(self, mock_console: Mock) -> None:
        """URLs without scheme or host should be rejected with an error message."""
        # Missing scheme
        result_no_scheme = _validate_direct_url("example.com/app.AppImage")
        assert result_no_scheme is None

        # Missing host
        result_no_host = _validate_direct_url("file:///relative/path")
        assert result_no_host is None

        calls = "".join(str(call) for call in mock_console.print.call_args_list)
        assert "Error: Invalid URL format" in calls


class TestValidateBasicFieldUpdates:
    """Tests for validate_basic_field_updates helper."""

    def test_invalid_regex_pattern_raises_value_error(self) -> None:
        """An invalid regex pattern in updates['pattern'] should raise ValueError."""
        updates = {"pattern": "[unclosed"}

        with pytest.raises(ValueError, match="Invalid regex pattern"):
            validate_basic_field_updates(updates)

    def test_invalid_checksum_algorithm_raises_value_error(self) -> None:
        """An unsupported checksum_algorithm should raise ValueError."""
        updates = {"checksum_algorithm": "sha999"}

        with pytest.raises(ValueError, match="Invalid checksum algorithm"):
            validate_basic_field_updates(updates)

    def test_valid_pattern_and_checksum_algorithm_pass_validation(self) -> None:
        """Valid regex pattern and checksum algorithm should not raise."""
        updates = {"pattern": r"^Test.*\\.AppImage$", "checksum_algorithm": "sha256"}

        # Should not raise
        validate_basic_field_updates(updates)

    @patch("appimage_updater.config.operations.console")
    def test_validate_direct_url_handles_exceptions(self, mock_console: Mock) -> None:
        """Non-string or malformed inputs should be caught and return None with details."""
        # Passing a non-string value should trigger the exception branch
        result = _validate_direct_url(123)  # type: ignore[arg-type]
        assert result is None

        calls = "".join(str(call) for call in mock_console.print.call_args_list)
        assert "Error: Invalid URL format" in calls
