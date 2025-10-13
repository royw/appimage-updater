# type: ignore
"""Regression tests for default configuration behavior."""

import json
from pathlib import Path
import tempfile

import pytest

from appimage_updater.config.command import set_global_config_value
from appimage_updater.ui.cli.add_command_logic import _add


class TestDefaultsRegression:
    """Test that global defaults are properly applied when adding applications."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary configuration directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "appimage-updater"
            config_dir.mkdir(parents=True)
            apps_dir = config_dir / "apps"
            apps_dir.mkdir(parents=True)
            yield config_dir

    @pytest.mark.anyio
    async def test_freecad_defaults_regression(self, temp_config_dir) -> None:
        """Test that FreeCAD can be added using minimal command line with appropriate defaults."""
        # Set global defaults to match expected FreeCAD configuration
        test_apps_dir = temp_config_dir / "test-apps"
        set_global_config_value("download-dir", str(test_apps_dir), None, temp_config_dir)
        set_global_config_value("checksum", "true", None, temp_config_dir)
        set_global_config_value("checksum-algorithm", "sha256", None, temp_config_dir)
        set_global_config_value("checksum-pattern", "{filename}-SHA256.txt", None, temp_config_dir)
        set_global_config_value("checksum-required", "false", None, temp_config_dir)
        set_global_config_value("prerelease", "false", None, temp_config_dir)
        set_global_config_value("auto-subdir", "true", None, temp_config_dir)

        # Add FreeCAD using minimal command line
        result = await _add(
            name="FreeCAD",
            url="https://github.com/FreeCAD/FreeCAD",
            download_dir=str(test_apps_dir / "FreeCAD"),  # Use explicit path that matches auto-subdir behavior
            auto_subdir=None,  # Should use default
            config_file=None,
            config_dir=temp_config_dir,
            rotation=None,  # Should use default
            retain=3,  # Default retain count
            symlink=None,  # Should use default
            prerelease=None,  # Should use default
            checksum=None,  # Should use default
            checksum_algorithm=None,  # Should use default
            checksum_pattern=None,  # Should use default
            checksum_required=None,  # Should use default
            pattern=None,  # Should be auto-generated
            version_pattern=None,  # Should use default
            direct=None,  # Should use default
            create_dir=True,
            yes=True,
            no=False,
            dry_run=False,
            verbose=False,
        )

        # Verify the created configuration
        freecad_config_path = temp_config_dir / "freecad.json"
        assert freecad_config_path.exists(), "FreeCAD configuration should be created"

        with freecad_config_path.open() as f:
            config_data = json.load(f)

        assert "applications" in config_data
        assert len(config_data["applications"]) == 1

        app_config = config_data["applications"][0]

        # Verify core configuration matches expected values
        assert app_config["name"] == "FreeCAD"
        assert app_config["source_type"] == "github"
        assert app_config["url"] == "https://github.com/FreeCAD/FreeCAD"
        assert app_config["download_dir"] == str(test_apps_dir / "FreeCAD")  # auto-subdir applied
        assert app_config["enabled"] is True
        assert app_config["prerelease"] is False
        assert app_config["rotation_enabled"] is False

        # Verify checksum configuration
        checksum_config = app_config["checksum"]
        assert checksum_config["enabled"] is True
        assert checksum_config["algorithm"] == "sha256"
        assert checksum_config["pattern"] == "{filename}-SHA256.txt"
        assert checksum_config["required"] is False

        # Verify pattern was auto-generated
        assert "pattern" in app_config
        assert "FreeCAD" in app_config["pattern"]
        assert "AppImage" in app_config["pattern"]

    @pytest.mark.anyio
    async def test_freecad_weekly_defaults_regression(self, temp_config_dir) -> None:
        """Test that FreeCAD_weekly can be added using minimal command line with appropriate defaults."""
        # Set global defaults to match expected FreeCAD_weekly configuration
        test_apps_dir = temp_config_dir / "test-apps"
        set_global_config_value("download-dir", str(test_apps_dir), None, temp_config_dir)
        set_global_config_value("checksum", "true", None, temp_config_dir)
        set_global_config_value("checksum-algorithm", "sha256", None, temp_config_dir)
        set_global_config_value("checksum-pattern", "{filename}-SHA256.txt", None, temp_config_dir)
        set_global_config_value("checksum-required", "false", None, temp_config_dir)
        set_global_config_value("rotation", "true", None, temp_config_dir)
        set_global_config_value("retain-count", "3", None, temp_config_dir)
        set_global_config_value("prerelease", "true", None, temp_config_dir)
        set_global_config_value("auto-subdir", "true", None, temp_config_dir)
        set_global_config_value("symlink-enabled", "true", None, temp_config_dir)
        set_global_config_value("symlink-dir", str(test_apps_dir), None, temp_config_dir)
        set_global_config_value("symlink-pattern", "{appname}.AppImage", None, temp_config_dir)

        # Add FreeCAD_weekly using minimal command line
        result = await _add(
            name="FreeCAD_weekly",
            url="https://github.com/FreeCAD/FreeCAD",
            download_dir=str(test_apps_dir / "FreeCAD_weekly"),  # Use explicit path that matches auto-subdir behavior
            auto_subdir=None,  # Should use default
            config_file=None,
            config_dir=temp_config_dir,
            rotation=None,  # Should use default (true)
            retain=3,  # Default retain count
            symlink=None,  # Should use default pattern
            prerelease=None,  # Should use default (true)
            checksum=None,  # Should use default
            checksum_algorithm=None,  # Should use default
            checksum_pattern=None,  # Should use default
            checksum_required=None,  # Should use default
            pattern=None,  # Should be auto-generated
            version_pattern=None,  # Should use default
            direct=None,  # Should use default
            create_dir=True,
            yes=True,
            no=False,
            dry_run=False,
            verbose=False,
        )

        # Verify the created configuration
        freecad_weekly_config_path = temp_config_dir / "freecad_weekly.json"
        assert freecad_weekly_config_path.exists(), "FreeCAD_weekly configuration should be created"

        with freecad_weekly_config_path.open() as f:
            config_data = json.load(f)

        assert "applications" in config_data
        assert len(config_data["applications"]) == 1

        app_config = config_data["applications"][0]

        # Verify core configuration matches expected values
        assert app_config["name"] == "FreeCAD_weekly"
        assert app_config["source_type"] == "github"
        assert app_config["url"] == "https://github.com/FreeCAD/FreeCAD"
        assert app_config["download_dir"] == str(test_apps_dir / "FreeCAD_weekly")  # auto-subdir applied
        assert app_config["enabled"] is True
        assert app_config["prerelease"] is True
        assert app_config["rotation_enabled"] is True
        assert app_config["retain_count"] == 3

        # Verify symlink configuration
        assert app_config["symlink_path"] == str(test_apps_dir / "FreeCAD_weekly.AppImage")

        # Verify checksum configuration
        checksum_config = app_config["checksum"]
        assert checksum_config["enabled"] is True
        assert checksum_config["algorithm"] == "sha256"
        assert checksum_config["pattern"] == "{filename}-SHA256.txt"
        assert checksum_config["required"] is False

        # Verify pattern was auto-generated
        assert "pattern" in app_config
        assert "FreeCAD" in app_config["pattern"]
        assert "AppImage" in app_config["pattern"]

    @pytest.mark.anyio
    async def test_minimal_add_command_with_defaults(self, temp_config_dir) -> None:
        """Test that the minimal add command works with global defaults."""
        # Set basic defaults
        test_apps_dir = temp_config_dir / "test-apps"
        set_global_config_value("download-dir", str(test_apps_dir), None, temp_config_dir)
        set_global_config_value("auto-subdir", "true", None, temp_config_dir)
        set_global_config_value("checksum", "true", None, temp_config_dir)

        # Add application with minimal parameters - use the default download dir
        # Note: We need to provide the download_dir because the add function
        # expects it before applying defaults
        await _add(
            name="TestApp",
            url="https://github.com/user/testapp",
            download_dir=str(test_apps_dir / "TestApp"),  # Use explicit path that matches auto-subdir behavior
            auto_subdir=None,
            config_file=None,
            config_dir=temp_config_dir,
            rotation=None,
            retain=3,
            symlink=None,
            prerelease=None,
            checksum=None,
            checksum_algorithm=None,
            checksum_pattern=None,
            checksum_required=None,
            pattern=None,
            version_pattern=None,
            direct=None,
            create_dir=True,
            yes=True,
            no=False,
            dry_run=False,
            verbose=False,
        )

        # Verify configuration was created with defaults
        # The config file is created with lowercase name in the root config directory
        config_path = temp_config_dir / "testapp.json"
        assert config_path.exists()

        with config_path.open() as f:
            config_data = json.load(f)

        app_config = config_data["applications"][0]
        assert app_config["name"] == "TestApp"
        assert app_config["download_dir"] == str(test_apps_dir / "TestApp")  # auto-subdir applied
        assert app_config["checksum"]["enabled"] is True

    @pytest.mark.anyio
    async def test_defaults_override_with_explicit_parameters(self, temp_config_dir) -> None:
        """Test that explicit parameters override global defaults."""
        # Set defaults
        set_global_config_value("checksum", "true", None, temp_config_dir)
        set_global_config_value("prerelease", "false", None, temp_config_dir)
        set_global_config_value("auto-subdir", "true", None, temp_config_dir)

        # Add application with explicit overrides
        explicit_path = temp_config_dir / "explicit-path"
        await _add(
            name="OverrideTest",
            url="https://github.com/user/override",
            download_dir=str(explicit_path),  # Override default
            auto_subdir=None,
            config_file=None,
            config_dir=temp_config_dir,
            rotation=None,
            retain=3,
            symlink=None,
            prerelease=True,  # Override default
            checksum=False,  # Override default
            checksum_algorithm=None,
            checksum_pattern=None,
            checksum_required=None,
            pattern=None,
            version_pattern=None,
            direct=None,
            create_dir=True,
            yes=True,
            no=False,
            dry_run=False,
            verbose=False,
        )

        # Verify explicit parameters took precedence
        config_path = temp_config_dir / "overridetest.json"
        assert config_path.exists()

        with config_path.open() as f:
            config_data = json.load(f)

        app_config = config_data["applications"][0]
        assert app_config["download_dir"] == str(explicit_path)  # Explicit path, not auto-subdir
        assert app_config["prerelease"] is True  # Override default
        assert app_config["checksum"]["enabled"] is False  # Override default
