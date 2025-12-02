from pathlib import Path
from typing import Any

import pytest

from appimage_updater.core.info_file_service import InfoFileService


class SimpleAppConfig:
    def __init__(self, name: str, download_dir: Path) -> None:
        self.name = name
        self.download_dir = download_dir


@pytest.fixture
def service() -> InfoFileService:
    return InfoFileService()


def test_find_info_file_strategy_1_uses_current_info_file(tmp_path: Path, service: InfoFileService) -> None:
    app_dir = tmp_path
    current = app_dir / "MyApp.AppImage.current"
    current.write_text("dummy")
    info_from_current = app_dir / "MyApp.AppImage.current.info"
    info_from_current.write_text("Version: 1.0.0")

    config = SimpleAppConfig("MyApp", app_dir)

    result = service.find_info_file(config)  # type: ignore[arg-type]

    assert result == info_from_current


def test_find_info_file_strategy_2_picks_latest_info(tmp_path: Path, service: InfoFileService) -> None:
    app_dir = tmp_path
    older = app_dir / "A.info"
    newer = app_dir / "B.info"
    older.write_text("Version: 0.9")
    newer.write_text("Version: 1.0")

    config = SimpleAppConfig("MyApp", app_dir)

    result = service.find_info_file(config)  # type: ignore[arg-type]

    assert result == newer


def test_find_info_file_strategy_3_standard_name(tmp_path: Path, service: InfoFileService) -> None:
    app_dir = tmp_path
    standard = app_dir / "MyApp.info"
    standard.write_text("Version: 2.0")

    config = SimpleAppConfig("MyApp", app_dir)

    result = service.find_info_file(config)  # type: ignore[arg-type]

    assert result == standard


def test_find_info_file_returns_none_when_directory_missing(service: InfoFileService, tmp_path: Path) -> None:
    missing_dir = tmp_path / "does_not_exist"
    config = SimpleAppConfig("MyApp", missing_dir)

    result = service.find_info_file(config)  # type: ignore[arg-type]

    assert result is None


def test_read_info_file_returns_none_when_missing(service: InfoFileService, tmp_path: Path) -> None:
    missing = tmp_path / "no.info"

    result = service.read_info_file(missing)

    assert result is None


def test_read_info_file_parses_simple_version(service: InfoFileService, tmp_path: Path) -> None:
    info_path = tmp_path / "MyApp.info"
    info_path.write_text("Version: 1.2.3")

    result = service.read_info_file(info_path)

    assert result == "1.2.3"


def test_read_info_file_extracts_version_from_complex_string(service: InfoFileService, tmp_path: Path) -> None:
    info_path = tmp_path / "MyApp.info"
    info_path.write_text("OpenRGB_0.9_x86_64_b5f46e3.AppImage")

    result = service.read_info_file(info_path)

    assert result == "0.9"


def test_read_info_file_cleans_legacy_and_rotation_suffix(service: InfoFileService, tmp_path: Path) -> None:
    info_path = tmp_path / "MyApp.info"
    info_path.write_text("vv3.3.0.current")

    result = service.read_info_file(info_path)

    # One leading "v" should remain, and rotation suffix removed
    assert result == "3.3.0"


def test_write_info_file_success(service: InfoFileService, tmp_path: Path) -> None:
    info_path = tmp_path / "subdir" / "MyApp.info"

    ok = service.write_info_file(info_path, "1.0.0")

    assert ok is True
    assert info_path.exists()
    assert info_path.read_text() == "Version: 1.0.0"


def test_write_info_file_handles_os_error(monkeypatch: Any, service: InfoFileService, tmp_path: Path) -> None:
    info_path = tmp_path / "MyApp.info"

    def fake_write_text(self: Path, _content: str) -> int:  # noqa: D401, ARG001
        """Simulate write error."""
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_text", fake_write_text)

    ok = service.write_info_file(info_path, "1.0.0")

    assert ok is False
