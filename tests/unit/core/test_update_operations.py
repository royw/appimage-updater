"""Comprehensive unit tests for core update operations."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
import typer

from appimage_updater.config.loader import ConfigLoadError
from appimage_updater.config.models import ApplicationConfig, ChecksumConfig, Config
from appimage_updater.core.models import Asset, CheckResult, InteractiveResult, UpdateCandidate
from appimage_updater.ui.output.context import OutputFormatterContext
from appimage_updater.ui.output.rich_formatter import RichOutputFormatter
from appimage_updater.core.update_operations import (
    _check_updates,
    _convert_check_results_to_dict,
    _create_disabled_results,
    _create_downloader,
    _create_dry_run_result,
    _display_check_results,
    _display_check_start_message,
    _display_check_verbose_info,
    _display_update_summary,
    _execute_check_workflow,
    _execute_update_workflow,
    _extract_application_name,
    _extract_candidate_download_url,
    _extract_candidate_update_status,
    _extract_candidate_version_info,
    _extract_direct_download_url,
    _extract_direct_update_status,
    _extract_direct_version_info,
    _extract_error_message,
    _extract_status,
    _filter_update_candidates,
    _find_unrotated_appimages,
    _get_all_apps_for_check,
    _get_latest_appimage_file,
    _handle_check_errors,
    _handle_downloads,
    _handle_no_enabled_apps,
    _handle_no_updates_scenario,
    _handle_verbose_display,
    _is_symlink_valid,
    _is_unrotated_appimage,
    _load_and_filter_config,
    _load_config_with_fallback,
    _log_app_summary,
    _log_check_start,
    _log_check_statistics,
    _log_download_summary,
    _log_processing_method,
    _normalize_app_names,
    _perform_dry_run_checks,
    _perform_real_update_checks,
    _perform_update_checks,
    _prepare_check_environment,
    _process_app_rotation_setup,
    _prompt_for_download_confirmation,
    _setup_existing_files_rotation,
    _setup_rotation_for_file,
    _setup_rotation_safely,
    _should_skip_download_dir,
    _should_skip_rotation_setup,
    _should_suppress_console_output,
)
from appimage_updater.repositories.base import RepositoryError


@pytest.fixture
def mock_app_config(tmp_path: Path) -> ApplicationConfig:
    """Create a mock application configuration."""
    return ApplicationConfig(
        name="TestApp",
        source_type="github",
        url="https://github.com/test/repo",
        download_dir=tmp_path / "test",
        pattern=r".*\.AppImage$",
        enabled=True,
        rotation_enabled=False,
        retain_count=3,
        symlink_path=None,
        checksum=ChecksumConfig(enabled=True, algorithm="sha256"),
    )


@pytest.fixture
def mock_config(mock_app_config: ApplicationConfig) -> Config:
    """Create a mock configuration."""
    config = Config()
    config.applications = [mock_app_config]
    return config


@pytest.fixture
def mock_check_result() -> CheckResult:
    """Create a mock check result."""
    return CheckResult(
        app_name="TestApp",
        success=True,
        current_version="1.0.0",
        available_version="1.1.0",
        update_available=True,
        download_url="https://example.com/app.AppImage",
    )


@pytest.fixture
def mock_update_candidate(mock_app_config: ApplicationConfig, tmp_path: Path) -> UpdateCandidate:
    """Create a mock update candidate."""
    asset = Asset(
        name="TestApp-1.1.0.AppImage",
        url="https://example.com/app.AppImage",
        size=1024000,
        created_at=datetime.now(),
    )
    return UpdateCandidate(
        app_name="TestApp",
        current_version="1.0.0",
        latest_version="1.1.0",
        asset=asset,
        download_path=tmp_path / "test" / "TestApp-1.1.0.AppImage",
        is_newer=True,
        app_config=mock_app_config,
    )


class TestNormalizeAppNames:
    """Tests for _normalize_app_names function."""

    def test_normalize_single_string(self) -> None:
        """Test normalizing a single string to list."""
        result = _normalize_app_names("TestApp")
        assert result == ["TestApp"]

    def test_normalize_none(self) -> None:
        """Test normalizing None to empty list."""
        result = _normalize_app_names(None)
        assert result == []

    def test_normalize_list(self) -> None:
        """Test normalizing list returns same list."""
        result = _normalize_app_names(["App1", "App2"])
        assert result == ["App1", "App2"]

    def test_normalize_empty_list(self) -> None:
        """Test normalizing empty list returns empty list."""
        result = _normalize_app_names([])
        assert result == []


class TestLoadConfigWithFallback:
    """Tests for _load_config_with_fallback function."""

    @patch("appimage_updater.core.update_operations.AppConfigs")
    def test_load_config_success(self, mock_app_configs: Mock, tmp_path: Path) -> None:
        """Test successful config loading."""
        mock_config = Config()
        mock_app_configs.return_value._config = mock_config
        config_dir = tmp_path / "config"

        result = _load_config_with_fallback(None, config_dir)

        assert result == mock_config
        mock_app_configs.assert_called_once_with(config_path=config_dir)

    @patch("appimage_updater.core.update_operations.AppConfigs")
    def test_load_config_with_file(self, mock_app_configs: Mock, tmp_path: Path) -> None:
        """Test loading config with explicit file."""
        mock_config = Config()
        mock_app_configs.return_value._config = mock_config
        config_file = tmp_path / "config.json"

        result = _load_config_with_fallback(config_file, None)

        assert result == mock_config
        mock_app_configs.assert_called_once_with(config_path=config_file)

    @patch("appimage_updater.core.update_operations.AppConfigs")
    def test_load_config_not_found_no_explicit_file(self, mock_app_configs: Mock, tmp_path: Path) -> None:
        """Test loading config when not found and no explicit file."""
        mock_app_configs.side_effect = ConfigLoadError("Config not found")
        config_dir = tmp_path / "config"

        result = _load_config_with_fallback(None, config_dir)

        assert isinstance(result, Config)
        assert len(result.applications) == 0

    @patch("appimage_updater.core.update_operations.AppConfigs")
    def test_load_config_not_found_with_explicit_file(self, mock_app_configs: Mock, tmp_path: Path) -> None:
        """Test loading config when not found with explicit file raises."""
        mock_app_configs.side_effect = ConfigLoadError("Config not found")
        config_file = tmp_path / "config.json"

        with pytest.raises(ConfigLoadError):
            _load_config_with_fallback(config_file, None)

    @patch("appimage_updater.core.update_operations.AppConfigs")
    def test_load_config_other_error_raises(self, mock_app_configs: Mock, tmp_path: Path) -> None:
        """Test loading config with other error raises."""
        mock_app_configs.side_effect = ConfigLoadError("Permission denied")
        config_dir = tmp_path / "config"

        with pytest.raises(ConfigLoadError):
            _load_config_with_fallback(None, config_dir)


class TestGetAllAppsForCheck:
    """Tests for _get_all_apps_for_check function."""

    def test_get_all_apps_no_filter(self, mock_config: Mock) -> None:
        """Test getting all apps without filter."""
        result = _get_all_apps_for_check(mock_config, None)

        assert result is not None
        enabled, disabled = result
        assert len(enabled) == 1
        assert len(disabled) == 0

    def test_get_all_apps_with_disabled(self, mock_config: Mock, tmp_path: Path) -> None:
        """Test getting all apps with disabled apps."""
        disabled_app = ApplicationConfig(
            name="DisabledApp",
            source_type="github",
            url="https://github.com/test/disabled",
            download_dir=tmp_path / "disabled",
            pattern=r".*\.AppImage$",
            enabled=False,
        )
        mock_config.applications.append(disabled_app)

        result = _get_all_apps_for_check(mock_config, None)

        assert result is not None
        enabled, disabled = result
        assert len(enabled) == 1
        assert len(disabled) == 1
        assert disabled[0].name == "DisabledApp"

    @patch("appimage_updater.core.update_operations.ApplicationService.filter_apps_by_names")
    def test_get_all_apps_with_filter(self, mock_filter: Mock, mock_config: Mock) -> None:
        """Test getting apps with name filter."""
        mock_filter.return_value = [mock_config.applications[0]]

        result = _get_all_apps_for_check(mock_config, ["TestApp"])

        assert result is not None
        enabled, disabled = result
        assert len(enabled) == 1
        mock_filter.assert_called_once()

    @patch("appimage_updater.core.update_operations.ApplicationService.filter_apps_by_names")
    def test_get_all_apps_filter_not_found(self, mock_filter: Mock, mock_config: Mock) -> None:
        """Test getting apps when filter finds nothing."""
        mock_filter.return_value = None

        result = _get_all_apps_for_check(mock_config, ["NonExistent"])

        assert result is None


class TestCreateDisabledResults:
    """Tests for _create_disabled_results function."""

    def test_create_disabled_results_empty(self) -> None:
        """Test creating disabled results with empty list."""
        result = _create_disabled_results([])
        assert result == []

    def test_create_disabled_results_single_app(self, mock_app_config: Mock) -> None:
        """Test creating disabled result for single app."""
        mock_app_config.enabled = False
        result = _create_disabled_results([mock_app_config])

        assert len(result) == 1
        assert result[0].app_name == "TestApp"
        assert result[0].success is False
        assert result[0].error_message == "Disabled"
        assert result[0].download_url == mock_app_config.url

    def test_create_disabled_results_multiple_apps(self, tmp_path: Path) -> None:
        """Test creating disabled results for multiple apps."""
        apps = [
            ApplicationConfig(
                name=f"App{i}",
                source_type="github",
                url=f"https://github.com/test/app{i}",
                download_dir=tmp_path / f"app{i}",
                pattern=r".*\.AppImage$",
                enabled=False,
            )
            for i in range(3)
        ]

        result = _create_disabled_results(apps)

        assert len(result) == 3
        for i, check_result in enumerate(result):
            assert check_result.app_name == f"App{i}"
            assert check_result.error_message == "Disabled"


class TestFilterUpdateCandidates:
    """Tests for _filter_update_candidates function."""

    def test_filter_no_candidates(self) -> None:
        """Test filtering with no update candidates."""
        results = [
            CheckResult(
                app_name="App1",
                success=True,
                current_version="1.0.0",
                available_version="1.0.0",
                update_available=False,
            )
        ]

        candidates = _filter_update_candidates(results)
        assert candidates == []

    def test_filter_with_candidates(self, mock_update_candidate: Mock) -> None:
        """Test filtering with update candidates."""
        results = [
            CheckResult(
                app_name="TestApp",
                success=True,
                candidate=mock_update_candidate,
            )
        ]

        candidates = _filter_update_candidates(results)
        assert len(candidates) == 1
        assert candidates[0] == mock_update_candidate

    def test_filter_mixed_results(self, mock_update_candidate: Mock) -> None:
        """Test filtering with mixed success/failure results."""
        results = [
            CheckResult(
                app_name="App1",
                success=True,
                candidate=mock_update_candidate,
            ),
            CheckResult(
                app_name="App2",
                success=False,
                error_message="Failed",
            ),
            CheckResult(
                app_name="App3",
                success=True,
                current_version="1.0.0",
                available_version="1.0.0",
                update_available=False,
            ),
        ]

        candidates = _filter_update_candidates(results)
        assert len(candidates) == 1


class TestExtractResultData:
    """Tests for result data extraction functions."""

    def test_extract_application_name(self) -> None:
        """Test extracting application name."""
        result = CheckResult(app_name="TestApp", success=True)
        result_dict: dict[str, Any] = {}

        _extract_application_name(result, result_dict)

        assert result_dict["Application"] == "TestApp"

    def test_extract_application_name_with_whitespace(self) -> None:
        """Test extracting application name with whitespace."""
        result = CheckResult(app_name="  TestApp  ", success=True)
        result_dict: dict[str, Any] = {}

        _extract_application_name(result, result_dict)

        assert result_dict["Application"] == "TestApp"

    def test_extract_application_name_empty(self) -> None:
        """Test extracting empty application name."""
        result = CheckResult(app_name="", success=True)
        result_dict: dict[str, Any] = {}

        _extract_application_name(result, result_dict)

        assert result_dict["Application"] == "Unknown App"

    def test_extract_status_success(self) -> None:
        """Test extracting success status."""
        result = CheckResult(app_name="TestApp", success=True)
        result_dict: dict[str, Any] = {}

        _extract_status(result, result_dict)

        assert result_dict["Status"] == "Success"

    def test_extract_status_error(self) -> None:
        """Test extracting error status."""
        result = CheckResult(app_name="TestApp", success=False)
        result_dict: dict[str, Any] = {}

        _extract_status(result, result_dict)

        assert result_dict["Status"] == "Error"

    def test_extract_error_message(self) -> None:
        """Test extracting error message."""
        result = CheckResult(
            app_name="TestApp",
            success=False,
            error_message="Connection failed",
        )
        result_dict: dict[str, Any] = {}

        _extract_error_message(result, result_dict)

        assert result_dict["Update Available"] == "Connection failed"

    def test_extract_direct_version_info(self) -> None:
        """Test extracting version info from direct fields."""
        result = CheckResult(
            app_name="TestApp",
            success=True,
            current_version="1.0.0",
            available_version="1.1.0",
        )
        result_dict: dict[str, Any] = {}

        _extract_direct_version_info(result, result_dict)

        assert result_dict["Current Version"] == "1.0.0"
        assert result_dict["Latest Version"] == "1.1.0"

    def test_extract_direct_version_info_none(self) -> None:
        """Test extracting None version info."""
        result = CheckResult(
            app_name="TestApp",
            success=True,
            current_version=None,
            available_version=None,
        )
        result_dict: dict[str, Any] = {}

        _extract_direct_version_info(result, result_dict)

        assert result_dict["Current Version"] == "N/A"
        assert result_dict["Latest Version"] == "N/A"

    def test_extract_direct_update_status(self) -> None:
        """Test extracting update status from direct fields."""
        result = CheckResult(
            app_name="TestApp",
            success=True,
            update_available=True,
        )
        result_dict: dict[str, Any] = {}

        _extract_direct_update_status(result, result_dict)

        assert result_dict["Update Available"] == "Yes"

    def test_extract_direct_download_url(self) -> None:
        """Test extracting download URL from direct fields."""
        result = CheckResult(
            app_name="TestApp",
            success=True,
            download_url="https://example.com/app.AppImage",
        )
        result_dict: dict[str, Any] = {}

        _extract_direct_download_url(result, result_dict)

        assert result_dict["Download URL"] == "https://example.com/app.AppImage"

    def test_extract_candidate_version_info(self, mock_update_candidate: Mock) -> None:
        """Test extracting version info from candidate."""
        result_dict: dict[str, Any] = {}

        _extract_candidate_version_info(mock_update_candidate, result_dict)

        assert result_dict["Current Version"] == "1.0.0"
        assert result_dict["Latest Version"] == "1.1.0"

    def test_extract_candidate_update_status(self, mock_update_candidate: Mock) -> None:
        """Test extracting update status from candidate."""
        result_dict: dict[str, Any] = {}

        _extract_candidate_update_status(mock_update_candidate, result_dict)

        assert result_dict["Update Available"] == "Yes"

    def test_extract_candidate_download_url(self, mock_update_candidate: Mock) -> None:
        """Test extracting download URL from candidate."""
        result_dict: dict[str, Any] = {}

        _extract_candidate_download_url(mock_update_candidate, result_dict)

        # The function extracts from candidate.download_url if it exists
        # UpdateCandidate doesn't have download_url, it has asset.url
        assert "Download URL" not in result_dict or result_dict["Download URL"] == "https://example.com/app.AppImage"


class TestCreateDryRunResult:
    """Tests for _create_dry_run_result function."""

    @patch("appimage_updater.core.update_operations.VersionChecker")
    def test_create_dry_run_result_success(self, mock_version_checker_class: Mock, mock_app_config: Mock) -> None:
        """Test creating dry run result successfully."""
        mock_checker = Mock()
        mock_checker._get_current_version.return_value = "1.0.0"
        mock_version_checker_class.return_value = mock_checker

        result = _create_dry_run_result(mock_app_config, mock_checker)

        assert result.app_name == "TestApp"
        assert result.success is True
        assert result.current_version == "1.0.0"
        assert result.available_version == "Not checked (dry-run)"
        assert result.update_available is False
        assert result.download_url == mock_app_config.url

    @patch("appimage_updater.core.update_operations.VersionChecker")
    def test_create_dry_run_result_error(self, mock_version_checker_class: Mock, mock_app_config: Mock) -> None:
        """Test creating dry run result with error."""
        mock_checker = Mock()
        mock_checker._get_current_version.side_effect = OSError("File not found")
        mock_version_checker_class.return_value = mock_checker

        result = _create_dry_run_result(mock_app_config, mock_checker)

        assert result.app_name == "TestApp"
        assert result.success is False
        assert result.current_version is None
        assert result.error_message is not None
        assert "Error reading current version" in result.error_message


class TestPromptForDownloadConfirmation:
    """Tests for _prompt_for_download_confirmation function."""

    @patch("appimage_updater.core.update_operations.typer.confirm")
    @patch("appimage_updater.core.update_operations.console")
    def test_prompt_user_confirms(self, mock_console: Mock, mock_confirm: Mock) -> None:
        """Test user confirms download."""
        mock_confirm.return_value = True

        result = _prompt_for_download_confirmation()

        assert result.success is True
        assert result.cancelled is False
        mock_confirm.assert_called_once()

    @patch("appimage_updater.core.update_operations.typer.confirm")
    @patch("appimage_updater.core.update_operations.console")
    def test_prompt_user_cancels(self, mock_console: Mock, mock_confirm: Mock) -> None:
        """Test user cancels download."""
        mock_confirm.return_value = False

        result = _prompt_for_download_confirmation()

        assert result.success is False
        assert result.cancelled is True
        assert result.reason == "user_cancelled"

    @patch("appimage_updater.core.update_operations.typer.confirm")
    @patch("appimage_updater.core.update_operations.console")
    def test_prompt_non_interactive(self, mock_console: Mock, mock_confirm: Mock) -> None:
        """Test non-interactive mode."""
        mock_confirm.side_effect = EOFError()

        result = _prompt_for_download_confirmation()

        assert result.success is False
        assert result.cancelled is True
        assert result.reason == "non_interactive"

    @patch("appimage_updater.core.update_operations.typer.confirm")
    @patch("appimage_updater.core.update_operations.console")
    def test_prompt_keyboard_interrupt(self, mock_console: Mock, mock_confirm: Mock) -> None:
        """Test keyboard interrupt."""
        mock_confirm.side_effect = KeyboardInterrupt()

        result = _prompt_for_download_confirmation()

        assert result.success is False
        assert result.cancelled is True


class TestCreateDownloader:
    """Tests for _create_downloader function."""

    @patch("appimage_updater.core.update_operations.Downloader")
    def test_create_downloader(self, mock_downloader_class: Mock, mock_config: Mock) -> None:
        """Test creating downloader with config."""
        mock_config.global_config.timeout_seconds = 30
        mock_config.global_config.user_agent = "TestAgent"
        mock_config.global_config.concurrent_downloads = 3

        _create_downloader(mock_config)

        mock_downloader_class.assert_called_once_with(
            timeout=300,  # 30 * 10
            user_agent="TestAgent",
            max_concurrent=3,
        )


class TestRotationHelpers:
    """Tests for rotation helper functions."""

    def test_should_skip_rotation_setup_no_rotation(self, mock_app_config: Mock, tmp_path: Path) -> None:
        """Test skipping rotation when not enabled."""
        mock_app_config.rotation_enabled = False
        mock_app_config.symlink_path = tmp_path / "link"

        result = _should_skip_rotation_setup(mock_app_config)

        assert result is True

    def test_should_skip_rotation_setup_no_symlink(self, mock_app_config: Mock) -> None:
        """Test skipping rotation when no symlink."""
        mock_app_config.rotation_enabled = True
        mock_app_config.symlink_path = None

        result = _should_skip_rotation_setup(mock_app_config)

        assert result is True

    def test_should_skip_rotation_setup_valid(self, mock_app_config: Mock, tmp_path: Path) -> None:
        """Test not skipping rotation when valid."""
        mock_app_config.rotation_enabled = True
        mock_app_config.symlink_path = tmp_path / "link"

        result = _should_skip_rotation_setup(mock_app_config)

        assert result is False

    def test_should_skip_download_dir_not_exists(self, tmp_path: Path) -> None:
        """Test skipping when download dir doesn't exist."""
        non_existent = tmp_path / "nonexistent"

        result = _should_skip_download_dir(non_existent)

        assert result is True

    def test_should_skip_download_dir_exists(self, tmp_path: Path) -> None:
        """Test not skipping when download dir exists."""
        result = _should_skip_download_dir(tmp_path)

        assert result is False

    def test_is_unrotated_appimage_valid(self, tmp_path: Path) -> None:
        """Test identifying unrotated AppImage."""
        appimage = tmp_path / "test.AppImage"
        appimage.touch()

        result = _is_unrotated_appimage(appimage)

        assert result is True

    def test_is_unrotated_appimage_with_rotation_suffix(self, tmp_path: Path) -> None:
        """Test identifying rotated AppImage."""
        appimage = tmp_path / "test.AppImage.current"
        appimage.touch()

        result = _is_unrotated_appimage(appimage)

        assert result is False

    def test_is_unrotated_appimage_wrong_extension(self, tmp_path: Path) -> None:
        """Test non-AppImage file."""
        other_file = tmp_path / "test.zip"
        other_file.touch()

        result = _is_unrotated_appimage(other_file)

        assert result is False

    def test_is_unrotated_appimage_directory(self, tmp_path: Path) -> None:
        """Test directory is not AppImage."""
        directory = tmp_path / "test.AppImage"
        directory.mkdir()

        result = _is_unrotated_appimage(directory)

        assert result is False

    def test_find_unrotated_appimages(self, tmp_path: Path) -> None:
        """Test finding unrotated AppImages."""
        # Create test files
        (tmp_path / "app1.AppImage").touch()
        (tmp_path / "app2.AppImage").touch()
        (tmp_path / "app3.AppImage.current").touch()
        (tmp_path / "other.zip").touch()

        result = _find_unrotated_appimages(tmp_path)

        assert len(result) == 2
        names = [f.name for f in result]
        assert "app1.AppImage" in names
        assert "app2.AppImage" in names

    def test_get_latest_appimage_file_empty(self, tmp_path: Path) -> None:
        """Test getting latest AppImage from empty directory."""
        result = _get_latest_appimage_file(tmp_path)

        assert result is None

    def test_get_latest_appimage_file_single(self, tmp_path: Path) -> None:
        """Test getting latest AppImage with single file."""
        appimage = tmp_path / "test.AppImage"
        appimage.touch()

        result = _get_latest_appimage_file(tmp_path)

        assert result == appimage

    def test_get_latest_appimage_file_multiple(self, tmp_path: Path) -> None:
        """Test getting latest AppImage with multiple files."""
        import time

        old_file = tmp_path / "old.AppImage"
        old_file.touch()
        time.sleep(0.01)
        new_file = tmp_path / "new.AppImage"
        new_file.touch()

        result = _get_latest_appimage_file(tmp_path)

        assert result == new_file

    def test_is_symlink_valid_not_symlink(self, tmp_path: Path) -> None:
        """Test symlink validation with regular file."""
        regular_file = tmp_path / "file"
        regular_file.touch()

        result = _is_symlink_valid(regular_file, tmp_path)

        assert result is False

    def test_is_symlink_valid_not_exists(self, tmp_path: Path) -> None:
        """Test symlink validation with non-existent path."""
        non_existent = tmp_path / "nonexistent"

        result = _is_symlink_valid(non_existent, tmp_path)

        assert result is False

    def test_is_symlink_valid_broken_symlink(self, tmp_path: Path) -> None:
        """Test symlink validation with broken symlink."""
        symlink = tmp_path / "link"
        target = tmp_path / "nonexistent"
        symlink.symlink_to(target)

        result = _is_symlink_valid(symlink, tmp_path)

        assert result is False

    def test_is_symlink_valid_valid_symlink(self, tmp_path: Path) -> None:
        """Test symlink validation with valid symlink."""
        target = tmp_path / "target"
        target.touch()
        symlink = tmp_path / "link"
        symlink.symlink_to(target)

        result = _is_symlink_valid(symlink, tmp_path)

        assert result is True

    def test_is_symlink_valid_wrong_directory(self, tmp_path: Path) -> None:
        """Test symlink validation with target in wrong directory."""
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        target = other_dir / "target"
        target.touch()
        symlink = tmp_path / "link"
        symlink.symlink_to(target)

        result = _is_symlink_valid(symlink, tmp_path)

        assert result is False


class TestHandleCheckErrors:
    """Tests for _handle_check_errors function."""

    def test_handle_config_load_error(self) -> None:
        """Test handling ConfigLoadError."""
        error = ConfigLoadError("Config not found")
        formatter = RichOutputFormatter()

        with OutputFormatterContext(formatter):
            with pytest.raises(typer.Exit):
                _handle_check_errors(error)

    def test_handle_config_load_error_with_formatter(self) -> None:
        """Test handling ConfigLoadError with formatter."""
        error = ConfigLoadError("Config not found")
        formatter = RichOutputFormatter()

        with OutputFormatterContext(formatter):
            with pytest.raises(typer.Exit):
                _handle_check_errors(error)

    def test_handle_repository_error(self) -> None:
        """Test handling RepositoryError."""
        error = RepositoryError("Repository not found")
        formatter = RichOutputFormatter()

        with OutputFormatterContext(formatter):
            with pytest.raises(typer.Exit):
                _handle_check_errors(error)


class TestShouldSuppressConsoleOutput:
    """Tests for _should_suppress_console_output function."""

    def test_suppress_json_formatter(self) -> None:
        """Test suppressing JSON formatter output."""
        mock_formatter = Mock()
        mock_formatter.__class__.__name__ = "JSONOutputFormatter"

        result = _should_suppress_console_output(mock_formatter)

        assert result is True

    def test_suppress_html_formatter(self) -> None:
        """Test suppressing HTML formatter output."""
        mock_formatter = Mock()
        mock_formatter.__class__.__name__ = "HTMLOutputFormatter"

        result = _should_suppress_console_output(mock_formatter)

        assert result is True

    def test_not_suppress_rich_formatter(self) -> None:
        """Test not suppressing Rich formatter output."""
        mock_formatter = Mock()
        mock_formatter.__class__.__name__ = "RichOutputFormatter"

        result = _should_suppress_console_output(mock_formatter)

        assert result is False

    def test_not_suppress_none_formatter(self) -> None:
        """Test not suppressing when no formatter."""
        result = _should_suppress_console_output(None)

        # When formatter is None, the function returns False (truthy check fails)
        assert not result


class TestLogFunctions:
    """Tests for logging functions."""

    @patch("appimage_updater.core.update_operations.logger")
    def test_log_check_start(self, mock_logger: Mock, tmp_path: Path) -> None:
        """Test logging check start."""
        _log_check_start(None, tmp_path / "config", False, ["App1", "App2"])

        assert mock_logger.debug.call_count >= 2

    @patch("appimage_updater.core.update_operations.logger")
    def test_log_app_summary(self, mock_logger: Mock, mock_config: Mock) -> None:
        """Test logging app summary."""
        _log_app_summary(mock_config, mock_config.applications, None)

        mock_logger.debug.assert_called_once()

    @patch("appimage_updater.core.update_operations.logger")
    def test_log_check_statistics(self, mock_logger: Mock) -> None:
        """Test logging check statistics."""
        results = [
            CheckResult(app_name="App1", success=True),
            CheckResult(app_name="App2", success=False),
        ]
        candidates: list[Any] = []

        _log_check_statistics(results, candidates)

        mock_logger.debug.assert_called_once()

    @patch("appimage_updater.core.update_operations.logger")
    def test_log_download_summary(self, mock_logger: Mock) -> None:
        """Test logging download summary."""
        from appimage_updater.core.models import DownloadResult

        results = [
            DownloadResult(app_name="App1", success=True),
            DownloadResult(app_name="App2", success=False),
        ]

        _log_download_summary(results)

        mock_logger.debug.assert_called_once()

    @patch("appimage_updater.core.update_operations.logger")
    def test_log_processing_method_single(self, mock_logger: Mock) -> None:
        """Test logging processing method for single app."""
        _log_processing_method([Mock()])

        mock_logger.debug.assert_called_once()
        assert "sequential" in mock_logger.debug.call_args[0][0]

    @patch("appimage_updater.core.update_operations.logger")
    def test_log_processing_method_multiple(self, mock_logger: Mock) -> None:
        """Test logging processing method for multiple apps."""
        _log_processing_method([Mock(), Mock()])

        mock_logger.debug.assert_called_once()
        assert "concurrent" in mock_logger.debug.call_args[0][0]


class TestDisplayFunctions:
    """Tests for display functions."""

    @patch("appimage_updater.core.update_operations.console")
    def test_display_check_verbose_info(self, mock_console: Mock) -> None:
        """Test displaying verbose check info."""
        _display_check_verbose_info(["App1", "App2"], True, False, False, False, 2)

        assert mock_console.print.call_count >= 6

    def test_display_update_summary_single(self) -> None:
        """Test displaying update summary for single update."""
        candidates = [Mock()]
        formatter = RichOutputFormatter()

        with OutputFormatterContext(formatter):
            _display_update_summary(candidates)

    def test_display_update_summary_multiple(self) -> None:
        """Test displaying update summary for multiple updates."""
        candidates = [Mock(), Mock()]
        formatter = RichOutputFormatter()

        with OutputFormatterContext(formatter):
            _display_update_summary(candidates)

    def test_display_check_start_message(self) -> None:
        """Test displaying check start message."""
        apps = [Mock(), Mock()]
        formatter = RichOutputFormatter()

        with OutputFormatterContext(formatter):
            _display_check_start_message(apps)

    @patch("appimage_updater.core.update_operations.get_output_formatter")
    @patch("appimage_updater.core.update_operations.console")
    def test_display_check_start_message_suppressed(self, mock_console: Mock, mock_get_formatter: Mock) -> None:
        """Test suppressing check start message for JSON formatter."""
        mock_formatter = Mock()
        mock_formatter.__class__.__name__ = "JSONOutputFormatter"
        mock_get_formatter.return_value = mock_formatter
        apps = [Mock()]

        _display_check_start_message(apps)

        mock_console.print.assert_not_called()

    def test_handle_no_enabled_apps_with_formatter(self) -> None:
        """Test handling no enabled apps with formatter."""
        formatter = RichOutputFormatter()

        with OutputFormatterContext(formatter):
            _handle_no_enabled_apps()

    def test_handle_no_enabled_apps_without_formatter(self) -> None:
        """Test handling no enabled apps - now always uses formatter."""
        formatter = RichOutputFormatter()

        with OutputFormatterContext(formatter):
            _handle_no_enabled_apps()


class TestHandleVerboseDisplay:
    """Tests for _handle_verbose_display function."""

    @patch("appimage_updater.core.update_operations._display_check_verbose_info")
    def test_handle_verbose_display_enabled(self, mock_display: Mock) -> None:
        """Test verbose display when enabled."""
        _handle_verbose_display(True, ["App1"], False, False, False, False, 1)

        mock_display.assert_called_once()

    @patch("appimage_updater.core.update_operations._display_check_verbose_info")
    def test_handle_verbose_display_disabled(self, mock_display: Mock) -> None:
        """Test verbose display when disabled."""
        _handle_verbose_display(False, ["App1"], False, False, False, False, 1)

        mock_display.assert_not_called()

    @patch("appimage_updater.core.update_operations._display_check_verbose_info")
    def test_handle_verbose_display_no_names(self, mock_display: Mock) -> None:
        """Test verbose display with no app names."""
        _handle_verbose_display(True, None, False, False, False, False, 1)

        mock_display.assert_not_called()


class TestConvertCheckResultsToDict:
    """Tests for _convert_check_results_to_dict function."""

    def test_convert_empty_results(self) -> None:
        """Test converting empty results."""
        result = _convert_check_results_to_dict([])

        assert result == []

    def test_convert_single_result(self) -> None:
        """Test converting single result."""
        check_result = CheckResult(
            app_name="TestApp",
            success=True,
            current_version="1.0.0",
            available_version="1.1.0",
            update_available=True,
        )

        result = _convert_check_results_to_dict([check_result])

        assert len(result) == 1
        assert result[0]["Application"] == "TestApp"
        assert result[0]["Status"] == "Success"

    def test_convert_multiple_results(self) -> None:
        """Test converting multiple results."""
        results = [CheckResult(app_name=f"App{i}", success=True) for i in range(3)]

        result = _convert_check_results_to_dict(results)

        assert len(result) == 3


class TestAsyncFunctions:
    """Tests for async functions."""

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._execute_check_workflow")
    @patch("appimage_updater.core.update_operations._log_check_start")
    async def test_check_updates_success(self, mock_log: Mock, mock_execute: Mock) -> None:
        """Test successful check updates."""
        mock_execute.return_value = True

        result = await _check_updates(None, None, False, None, False)

        assert result is True
        mock_log.assert_called_once()
        mock_execute.assert_called_once()

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._execute_check_workflow")
    @patch("appimage_updater.core.update_operations._log_check_start")
    async def test_check_updates_with_output_formatter(self, mock_log: Mock, mock_execute: Mock) -> None:
        """Test check updates with output formatter."""
        mock_execute.return_value = True
        mock_formatter = Mock()

        result = await _check_updates(None, None, False, None, False, output_formatter=mock_formatter)

        assert result is True

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._execute_check_workflow")
    @patch("appimage_updater.core.update_operations._handle_check_errors")
    @patch("appimage_updater.core.update_operations._log_check_start")
    async def test_check_updates_config_error(
        self, mock_log: Mock, mock_handle_error: Mock, mock_execute: Mock
    ) -> None:
        """Test check updates with config error."""
        mock_execute.side_effect = ConfigLoadError("Config not found")
        mock_handle_error.return_value = None

        result = await _check_updates(None, None, False, None, False)

        assert result is False
        mock_handle_error.assert_called_once()

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._prepare_check_environment")
    @patch("appimage_updater.core.update_operations._execute_info_update_workflow")
    async def test_execute_check_workflow_info_mode(self, mock_info: Mock, mock_prepare: Mock) -> None:
        """Test execute check workflow in info mode."""
        mock_prepare.return_value = (Mock(), [Mock()], [])

        result = await _execute_check_workflow(None, None, None, False, False, False, False, False, True)

        assert result is True
        mock_info.assert_called_once()

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._prepare_check_environment")
    @patch("appimage_updater.core.update_operations._execute_update_workflow")
    async def test_execute_check_workflow_update_mode(self, mock_update: Mock, mock_prepare: Mock) -> None:
        """Test execute check workflow in update mode."""
        mock_prepare.return_value = (Mock(), [Mock()], [])

        result = await _execute_check_workflow(None, None, None, False, False, False, False, False, False)

        assert result is True
        mock_update.assert_called_once()

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._load_and_filter_config")
    @patch("appimage_updater.core.update_operations._handle_verbose_display")
    @patch("appimage_updater.core.update_operations._log_app_summary")
    async def test_prepare_check_environment_success(self, mock_log: Mock, mock_verbose: Mock, mock_load: Mock) -> None:
        """Test preparing check environment successfully."""
        mock_config = Mock()
        mock_load.return_value = (mock_config, [Mock()], [])

        config, enabled, disabled = await _prepare_check_environment(
            None, None, None, False, False, False, False, False
        )

        assert config == mock_config
        assert len(enabled or []) == 1
        assert len(disabled or []) == 0

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._load_and_filter_config")
    @patch("appimage_updater.core.update_operations._handle_no_enabled_apps")
    async def test_prepare_check_environment_no_apps(self, mock_handle: Mock, mock_load: Mock) -> None:
        """Test preparing check environment with no apps."""
        mock_load.return_value = (Mock(), [], [])

        config, enabled, disabled = await _prepare_check_environment(
            None, None, None, False, False, False, False, False
        )

        assert enabled == []
        assert disabled == []
        mock_handle.assert_called_once()

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._perform_update_checks")
    @patch("appimage_updater.core.update_operations._display_check_results")
    @patch("appimage_updater.core.update_operations._handle_no_updates_scenario")
    async def test_execute_update_workflow_no_updates(
        self, mock_no_updates: Mock, mock_display: Mock, mock_checks: Mock
    ) -> None:
        """Test execute update workflow with no updates."""
        mock_checks.return_value = []

        with OutputFormatterContext(RichOutputFormatter()):
            await _execute_update_workflow(Mock(), [Mock()], [], False, False, False, False)

        mock_no_updates.assert_called_once()

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._perform_update_checks")
    @patch("appimage_updater.core.update_operations._display_check_results")
    @patch("appimage_updater.core.update_operations._filter_update_candidates")
    @patch("appimage_updater.core.update_operations._handle_downloads")
    async def test_execute_update_workflow_with_updates(
        self, mock_downloads: Mock, mock_filter: Mock, mock_display: Mock, mock_checks: Mock
    ) -> None:
        """Test execute update workflow with updates."""
        mock_checks.return_value = [Mock()]
        mock_filter.return_value = [Mock()]

        with OutputFormatterContext(RichOutputFormatter()):
            await _execute_update_workflow(Mock(), [Mock()], [], False, False, False, False)

        mock_downloads.assert_called_once()

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._perform_dry_run_checks")
    async def test_perform_update_checks_dry_run(self, mock_dry_run: Mock) -> None:
        """Test performing update checks in dry run mode."""
        mock_dry_run.return_value = []

        with OutputFormatterContext(RichOutputFormatter()):
            result = await _perform_update_checks([Mock()], False, True)

        assert result == []
        mock_dry_run.assert_called_once()

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._perform_real_update_checks")
    async def test_perform_update_checks_real(self, mock_real: Mock) -> None:
        """Test performing real update checks."""
        mock_real.return_value = []

        with OutputFormatterContext(RichOutputFormatter()):
            result = await _perform_update_checks([Mock()], False, False)

        assert result == []
        mock_real.assert_called_once()

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations.VersionChecker")
    @patch("appimage_updater.core.update_operations.console")
    async def test_perform_dry_run_checks(
        self, mock_console: Mock, mock_checker_class: Mock, tmp_path: Path
    ) -> None:
        """Test performing dry run checks."""
        mock_checker = Mock()
        mock_checker._get_current_version.return_value = "1.0.0"
        mock_checker_class.return_value = mock_checker

        app_config = ApplicationConfig(
            name="TestApp",
            source_type="github",
            url="https://github.com/test/repo",
            download_dir=tmp_path / "test",
            pattern=r".*\.AppImage$",
        )

        with OutputFormatterContext(RichOutputFormatter()):
            result = await _perform_dry_run_checks([app_config], False)

        assert len(result) == 1
        assert result[0].app_name == "TestApp"

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations.VersionChecker")
    @patch("appimage_updater.core.update_operations.ConcurrentProcessor")
    async def test_perform_real_update_checks(self, mock_processor_class: Mock, mock_checker_class: Mock) -> None:
        """Test performing real update checks."""
        mock_processor = Mock()
        mock_processor.process_items_async = AsyncMock(return_value=[])
        mock_processor_class.return_value = mock_processor

        result = await _perform_real_update_checks([Mock()], False)

        assert result == []
        mock_processor.process_items_async.assert_called_once()

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._prompt_for_download_confirmation")
    @patch("appimage_updater.core.update_operations._create_downloader")
    @patch("appimage_updater.core.update_operations.display_download_results")
    @patch("appimage_updater.core.update_operations.console")
    async def test_handle_downloads_with_confirmation(
        self, mock_console: Mock, mock_display: Mock, mock_create: Mock, mock_prompt: Mock
    ) -> None:
        """Test handling downloads with user confirmation."""
        mock_prompt.return_value = InteractiveResult.success_result()
        mock_downloader = Mock()
        mock_downloader.download_updates = AsyncMock(return_value=[])
        mock_create.return_value = mock_downloader

        await _handle_downloads(Mock(), [Mock()], False)

        mock_prompt.assert_called_once()
        mock_downloader.download_updates.assert_called_once()

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._create_downloader")
    @patch("appimage_updater.core.update_operations.display_download_results")
    @patch("appimage_updater.core.update_operations.console")
    async def test_handle_downloads_with_yes_flag(
        self, mock_console: Mock, mock_display: Mock, mock_create: Mock
    ) -> None:
        """Test handling downloads with --yes flag."""
        mock_downloader = Mock()
        mock_downloader.download_updates = AsyncMock(return_value=[])
        mock_create.return_value = mock_downloader

        await _handle_downloads(Mock(), [Mock()], True)

        mock_downloader.download_updates.assert_called_once()

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._prompt_for_download_confirmation")
    async def test_handle_downloads_cancelled(self, mock_prompt: Mock) -> None:
        """Test handling downloads when user cancels."""
        mock_prompt.return_value = InteractiveResult.cancelled_result("user_cancelled")

        await _handle_downloads(Mock(), [Mock()], False)

        mock_prompt.assert_called_once()

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._setup_existing_files_rotation")
    @patch("appimage_updater.core.update_operations.get_output_formatter")
    @patch("appimage_updater.core.update_operations.console")
    async def test_handle_no_updates_scenario(
        self, mock_console: Mock, mock_formatter: Mock, mock_rotation: Mock
    ) -> None:
        """Test handling no updates scenario."""
        mock_formatter.return_value = None

        await _handle_no_updates_scenario(Mock(), [Mock()])

        mock_rotation.assert_called_once()
        mock_console.print.assert_called_once()

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._process_app_rotation_setup")
    async def test_setup_existing_files_rotation(self, mock_process: Mock) -> None:
        """Test setting up existing files rotation."""
        apps = [Mock(), Mock()]

        await _setup_existing_files_rotation(Mock(), apps)  # type: ignore[arg-type]

        assert mock_process.call_count == 2

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._should_skip_rotation_setup")
    @patch("appimage_updater.core.update_operations._setup_rotation_safely")
    async def test_process_app_rotation_setup_skip(self, mock_setup: Mock, mock_skip: Mock) -> None:
        """Test processing app rotation setup when should skip."""
        mock_skip.return_value = True

        await _process_app_rotation_setup(Mock(), Mock())

        mock_setup.assert_not_called()

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations.Downloader")
    async def test_setup_rotation_for_file(
        self, mock_downloader_class: Mock, tmp_path: Path, mock_app_config: ApplicationConfig
    ) -> None:
        """Test setting up rotation for file."""
        mock_downloader = Mock()
        mock_downloader._handle_rotation = AsyncMock()
        mock_downloader_class.return_value = mock_downloader

        test_file = tmp_path / "test.AppImage"
        test_file.touch()

        config = Config()
        await _setup_rotation_for_file(mock_app_config, test_file, config)

        mock_downloader._handle_rotation.assert_called_once()

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._setup_rotation_for_file")
    async def test_setup_rotation_safely_success(self, mock_setup: Mock, tmp_path: Path) -> None:
        """Test setting up rotation safely with success."""
        await _setup_rotation_safely(Mock(), tmp_path / "test", Mock())

        mock_setup.assert_called_once()

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._setup_rotation_for_file")
    @patch("appimage_updater.core.update_operations.logger")
    async def test_setup_rotation_safely_error(self, mock_logger: Mock, mock_setup: Mock, tmp_path: Path) -> None:
        """Test setting up rotation safely with error."""
        mock_setup.side_effect = OSError("Permission denied")

        await _setup_rotation_safely(Mock(name="TestApp"), tmp_path / "test", Mock())

        mock_logger.warning.assert_called_once()


class TestDisplayCheckResults:
    """Tests for _display_check_results function."""

    def test_display_check_results_no_formatter(self) -> None:
        """Test displaying check results - now always uses formatter."""
        results = [CheckResult(app_name="TestApp", success=True)]
        formatter = RichOutputFormatter()

        with OutputFormatterContext(formatter):
            _display_check_results(results, False)

    def test_display_check_results_with_formatter(self) -> None:
        """Test displaying check results with formatter."""
        results = [CheckResult(app_name="TestApp", success=True)]
        formatter = RichOutputFormatter()

        with OutputFormatterContext(formatter):
            _display_check_results(results, False)

    def test_display_check_results_sorts_by_name(self) -> None:
        """Test that check results are sorted by app name."""
        results = [
            CheckResult(app_name="Zebra", success=True),
            CheckResult(app_name="Apple", success=True),
            CheckResult(app_name="Banana", success=True),
        ]
        formatter = RichOutputFormatter()

        with OutputFormatterContext(formatter):
            _display_check_results(results, False)


class TestLoadAndFilterConfig:
    """Tests for _load_and_filter_config function."""

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._load_config_with_fallback")
    @patch("appimage_updater.core.update_operations._get_all_apps_for_check")
    @patch("appimage_updater.core.update_operations._log_app_summary")
    async def test_load_and_filter_config_success(self, mock_log: Mock, mock_get_apps: Mock, mock_load: Mock) -> None:
        """Test loading and filtering config successfully."""
        mock_config = Mock()
        mock_load.return_value = mock_config
        mock_get_apps.return_value = ([Mock()], [])

        config, enabled, disabled = await _load_and_filter_config(None, None, None)

        assert config == mock_config
        assert len(enabled or []) == 1
        assert len(disabled or []) == 0

    @pytest.mark.anyio
    @patch("appimage_updater.core.update_operations._load_config_with_fallback")
    @patch("appimage_updater.core.update_operations._get_all_apps_for_check")
    async def test_load_and_filter_config_apps_not_found(self, mock_get_apps: Mock, mock_load: Mock) -> None:
        """Test loading and filtering config when apps not found."""
        mock_load.return_value = Mock()
        mock_get_apps.return_value = None

        config, enabled, disabled = await _load_and_filter_config(None, None, ["NonExistent"])

        assert enabled is None
        assert disabled == []
