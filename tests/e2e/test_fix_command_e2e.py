"""End-to-end tests for the fix command."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import time

import pytest

from appimage_updater.commands.fix_command import FixCommand
from appimage_updater.commands.parameters import FixParams
from appimage_updater.config.models import ApplicationConfig, ChecksumConfig
from appimage_updater.ui.output.context import OutputFormatterContext
from appimage_updater.ui.output.rich_formatter import RichOutputFormatter
from tests.e2e.conftest import MockHTTPResponse


def configure_mock_github_releases(mock_http_client, tag_name="v1.0.0", app_name="TestApp"):
    """Configure mock GitHub releases API response."""

    mock_releases_response = MockHTTPResponse(
        status_code=200,
        json_data=[
            {
                "tag_name": tag_name,
                "name": f"{app_name} {tag_name.lstrip('v')}",
                "prerelease": False,
                "published_at": "2024-01-01T00:00:00Z",
                "assets": [
                    {
                        "name": f"{app_name}-{tag_name.lstrip('v')}.AppImage",
                        "browser_download_url": f"https://github.com/test/{app_name.lower()}/releases/download/{tag_name}/{app_name}-{tag_name.lstrip('v')}.AppImage",
                        "size": 1000000,
                        "content_type": "application/octet-stream",
                    }
                ],
            }
        ],
    )

    mock_http_client.configure_response(
        f"https://api.github.com/repos/test/{app_name.lower()}/releases", mock_releases_response
    )


@pytest.fixture
def temp_app_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def app_config(temp_app_dir: Path):
    """Create a test application configuration."""
    return ApplicationConfig(
        name="TestApp",
        source_type="github",
        url="https://github.com/test/testapp",
        download_dir=str(temp_app_dir),
        pattern=r"TestApp.*\.AppImage$",
        enabled=True,
        rotation_enabled=True,
        symlink_path=str(temp_app_dir / "TestApp.AppImage"),
        retain_count=3,
        checksum=ChecksumConfig(enabled=False),
    )


@pytest.fixture
def config_file(temp_app_dir: Path, app_config: ApplicationConfig):
    """Create a temporary config file."""
    config_data = {
        "applications": [
            {
                "name": app_config.name,
                "source_type": app_config.source_type,
                "url": app_config.url,
                "download_dir": str(temp_app_dir),  # Convert to string
                "pattern": app_config.pattern,
                "version_pattern": None,
                "basename": None,
                "enabled": app_config.enabled,
                "prerelease": False,
                "checksum": {
                    "enabled": app_config.checksum.enabled,
                    "pattern": "",
                    "algorithm": "sha256",
                    "required": False,
                },
                "rotation_enabled": app_config.rotation_enabled,
                "symlink_path": str(temp_app_dir / "TestApp.AppImage"),  # Convert to string
                "retain_count": app_config.retain_count,
            }
        ]
    }

    config_file = temp_app_dir / "config.json"
    config_file.write_text(json.dumps(config_data, indent=2))
    return config_file


@pytest.mark.anyio
async def test_fix_command_e2e_basic_repair(
    mock_http_client,  # This is the autouse fixture from conftest.py
    temp_app_dir: Path,
    app_config: ApplicationConfig,
    config_file: Path,
):
    """Test basic fix command functionality - repairs broken symlink."""
    # Configure mock HTTP responses
    configure_mock_github_releases(mock_http_client)

    # Create AppImage file but no symlink
    appimage_file = temp_app_dir / "TestApp-1.0.0.AppImage.current"
    appimage_file.write_bytes(b"fake appimage content")

    # Verify initial state - no symlink exists
    symlink_path = temp_app_dir / "TestApp.AppImage"
    assert not symlink_path.exists()
    assert appimage_file.exists()

    # Run fix command
    params = FixParams(app_name="TestApp", config_dir=temp_app_dir, debug=False)
    command = FixCommand(params)

    with OutputFormatterContext(RichOutputFormatter()):
        result = await command.execute()

    # Verify fix worked
    assert result.success
    assert symlink_path.exists()
    assert symlink_path.is_symlink()
    assert symlink_path.resolve() == appimage_file

    # Verify .info file was created
    info_file = appimage_file.with_suffix(appimage_file.suffix + ".info")
    assert info_file.exists()


@pytest.mark.anyio
async def test_fix_command_e2e_orphaned_info_cleanup(
    mock_http_client,  # This is the autouse fixture from conftest.py
    temp_app_dir: Path,
    app_config: ApplicationConfig,
    config_file: Path,
):
    """Test fix command cleans up orphaned .current.info files."""
    # Configure mock HTTP responses
    configure_mock_github_releases(mock_http_client)
    # Create current AppImage file with matching .info file
    current_file = temp_app_dir / "TestApp-1.0.0.AppImage.current"
    current_file.write_bytes(b"fake appimage content")

    valid_info = temp_app_dir / "TestApp-1.0.0.AppImage.current.info"
    valid_info.write_text("Version: 1.0.0\n")

    # Create orphaned .current.info files (no matching .current files)
    orphaned_1 = temp_app_dir / "OldApp-2.0.0.AppImage.current.info"
    orphaned_1.write_text("Version: 2.0.0\n")

    orphaned_2 = temp_app_dir / "AnotherApp-3.0.0.AppImage.current.info"
    orphaned_2.write_text("Version: 3.0.0\n")

    # Create non-.current.info files (should NOT be removed)
    regular_info = temp_app_dir / "RegularApp-1.0.0.AppImage.info"
    regular_info.write_text("Version: 1.0.0\n")

    old_info = temp_app_dir / "TestApp-0.9.0.AppImage.old.info"
    old_info.write_text("Version: 0.9.0\n")

    # Verify initial state
    assert current_file.exists()
    assert valid_info.exists()
    assert orphaned_1.exists()
    assert orphaned_2.exists()
    assert regular_info.exists()
    assert old_info.exists()

    # Run fix command

    params = FixParams(app_name="TestApp", config_dir=temp_app_dir, debug=False)
    command = FixCommand(params)

    with OutputFormatterContext(RichOutputFormatter()):
        result = await command.execute()

    # Verify fix worked and orphaned files were cleaned up
    assert result.success
    assert current_file.exists()
    assert valid_info.exists()
    assert regular_info.exists()
    assert old_info.exists()

    # Orphaned .current.info files should be removed
    assert not orphaned_1.exists()
    assert not orphaned_2.exists()

    # Verify symlink was created
    symlink_path = temp_app_dir / "TestApp.AppImage"
    assert symlink_path.exists()
    assert symlink_path.is_symlink()


@pytest.mark.anyio
async def test_fix_command_e2e_broken_symlink_repair(
    mock_http_client,  # This is the autouse fixture from conftest.py
    temp_app_dir: Path,
    app_config: ApplicationConfig,
    config_file: Path,
):
    """Test fix command repairs broken symlinks."""
    # Configure mock HTTP responses
    configure_mock_github_releases(mock_http_client)

    # Create AppImage file
    appimage_file = temp_app_dir / "TestApp-1.0.0.AppImage.current"
    appimage_file.write_bytes(b"fake appimage content")

    # Create broken symlink pointing to non-existent file
    symlink_path = temp_app_dir / "TestApp.AppImage"
    symlink_path.symlink_to(temp_app_dir / "non-existent.AppImage")

    # Verify initial state - broken symlink exists
    assert symlink_path.is_symlink()
    assert not symlink_path.resolve().exists()

    # Run fix command

    params = FixParams(app_name="TestApp", config_dir=temp_app_dir, debug=False)
    command = FixCommand(params)

    with OutputFormatterContext(RichOutputFormatter()):
        result = await command.execute()

    # Verify fix worked
    assert result.success
    assert symlink_path.exists()
    assert symlink_path.is_symlink()
    assert symlink_path.resolve() == appimage_file


@pytest.mark.anyio
async def test_fix_command_e2e_fallback_to_recent_file(
    mock_http_client,  # This is the autouse fixture from conftest.py
    temp_app_dir: Path,
    app_config: ApplicationConfig,
    config_file: Path,
):
    """Test fix command falls back to most recent AppImage when no .current file exists."""
    # Configure mock HTTP responses
    configure_mock_github_releases(mock_http_client)

    # Create regular AppImage files (no .current files)
    old_file = temp_app_dir / "TestApp-0.9.0.AppImage"
    old_file.write_bytes(b"old version")

    recent_file = temp_app_dir / "TestApp-1.0.0.AppImage"
    recent_file.write_bytes(b"new version")

    # Make recent file actually newer

    time.sleep(0.1)  # Ensure different timestamps
    recent_file.touch()

    # Verify initial state - no .current files
    current_files = list(temp_app_dir.glob("*.current"))
    assert len(current_files) == 0

    # Run fix command

    params = FixParams(app_name="TestApp", config_dir=temp_app_dir, debug=False)
    command = FixCommand(params)

    with OutputFormatterContext(RichOutputFormatter()):
        result = await command.execute()

    # Verify fix worked - should use most recent file
    assert result.success

    symlink_path = temp_app_dir / "TestApp.AppImage"
    assert symlink_path.exists()
    assert symlink_path.is_symlink()
    assert symlink_path.resolve() == recent_file

    # Verify .info file was created for the recent file
    info_file = recent_file.with_suffix(recent_file.suffix + ".info")
    assert info_file.exists()


@pytest.mark.anyio
async def test_fix_command_e2e_no_appimage_files(
    mock_http_client,  # This is the autouse fixture from conftest.py
    temp_app_dir: Path,
    app_config: ApplicationConfig,
    config_file: Path,
):
    """Test fix command fails gracefully when no AppImage files exist."""
    # Configure mock HTTP responses
    configure_mock_github_releases(mock_http_client)

    # Verify directory is empty
    appimage_files = list(temp_app_dir.glob("*.AppImage*"))
    assert len(appimage_files) == 0

    # Run fix command

    params = FixParams(app_name="TestApp", config_dir=temp_app_dir, debug=False)
    command = FixCommand(params)

    with OutputFormatterContext(RichOutputFormatter()):
        result = await command.execute()

    # Verify fix failed appropriately
    assert not result.success
    assert result.exit_code == 1


@pytest.mark.anyio
async def test_fix_command_e2e_no_symlink_configured(
    mock_http_client,  # This is the autouse fixture from conftest.py
    temp_app_dir: Path,
    config_file: Path,
):
    """Test fix command fails when no symlink is configured."""
    # Configure mock HTTP responses
    configure_mock_github_releases(mock_http_client)

    # Create config without symlink
    config_data = {
        "applications": [
            {
                "name": "TestApp",
                "source_type": "github",
                "url": "https://github.com/test/testapp",
                "download_dir": str(temp_app_dir),  # Convert to string
                "pattern": r"TestApp.*\.AppImage$",
                "enabled": True,
                "rotation_enabled": False,  # No symlink
                "symlink_path": None,
                "retain_count": 3,
                "checksum": {"enabled": False, "pattern": "", "algorithm": "sha256", "required": False},
            }
        ]
    }

    config_file.write_text(json.dumps(config_data, indent=2))

    # Create AppImage file
    appimage_file = temp_app_dir / "TestApp-1.0.0.AppImage"
    appimage_file.write_bytes(b"fake appimage content")

    # Run fix command

    params = FixParams(app_name="TestApp", config_dir=temp_app_dir, debug=False)
    command = FixCommand(params)

    with OutputFormatterContext(RichOutputFormatter()):
        result = await command.execute()

    # Verify fix failed appropriately
    assert not result.success
    assert result.exit_code == 1
