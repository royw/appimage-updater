# type: ignore
from pathlib import Path

from appimage_updater.main import app


def test_integration_smoke_test(e2e_environment, runner) -> None:
    """Smoke test to ensure basic CLI functionality works."""
    # Test that the app can be invoked without crashing
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "AppImage update manager" in result.stdout

    # Test that commands are available
    result = runner.invoke(app, ["check", "--help"])
    assert result.exit_code == 0
    assert "Check for updates to configured applications" in result.stdout

    # init command removed - config directory is now created automatically

    result = runner.invoke(app, ["list", "--help"])
    assert result.exit_code == 0
    assert "List all configured applications" in result.stdout

    result = runner.invoke(app, ["show", "--help"])
    assert result.exit_code == 0
    assert "Show detailed information about applications" in result.stdout

    result = runner.invoke(app, ["add", "--help"])
    assert result.exit_code == 0
    assert "Add a new application to the configuration" in result.stdout


def test_version_option(e2e_environment, runner) -> None:
    """Test the --version option displays version and exits."""
    import re
    import tomllib

    # Read version from pyproject.toml
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)
    expected_version = pyproject["project"]["version"]

    # Test --version flag
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "AppImage Updater" in result.stdout

    # Strip ANSI color codes to check version
    clean_output = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
    assert expected_version in clean_output

    # Test -V short flag
    result_short = runner.invoke(app, ["-V"])
    assert result_short.exit_code == 0
    assert "AppImage Updater" in result_short.stdout

    # Strip ANSI color codes to check version
    clean_output_short = re.sub(r"\x1b\[[0-9;]*m", "", result_short.stdout)
    assert expected_version in clean_output_short

    # Version output should be identical for both flags
    assert result.stdout == result_short.stdout
