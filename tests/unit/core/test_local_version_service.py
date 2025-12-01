from pathlib import Path
from types import SimpleNamespace

import pytest

from appimage_updater.config.models import ApplicationConfig
from appimage_updater.core.info_file_service import InfoFileService
from appimage_updater.core.local_version_service import LocalVersionService
from appimage_updater.core.version_parser import VersionParser


class DummyInfoFileService(InfoFileService):
    def __init__(self, info_file: Path | None, version: str | None) -> None:
        self._info_file = info_file
        self._version = version

    def find_info_file(self, app_config: ApplicationConfig) -> Path | None:  # type: ignore[override]
        return self._info_file

    def read_info_file(self, path: Path) -> str | None:  # type: ignore[override]
        return self._version


class DummyVersionParser(VersionParser):
    def __init__(self, filename_version: str | None = None, normalized: str | None = None) -> None:
        self._filename_version = filename_version
        self._normalized = normalized or (filename_version or "")

    def extract_version_from_filename(self, filename: str) -> str | None:  # type: ignore[override]
        return self._filename_version

    def normalize_version_string(self, version: str) -> str:  # type: ignore[override]
        return self._normalized


class TestLocalVersionService:
    def test_get_current_version_prefers_info_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        info_path = tmp_path / "TestApp.info"
        info_service = DummyInfoFileService(info_path, "1.2.3")
        parser = DummyVersionParser(normalized="1.2.3-normalized")

        svc = LocalVersionService(version_parser=parser, info_service=info_service)
        app_config = SimpleNamespace(download_dir=tmp_path)

        result = svc.get_current_version(app_config)  # type: ignore[arg-type]

        assert result == "1.2.3-normalized"

    def test_get_current_version_uses_current_file_when_no_info(self, tmp_path: Path) -> None:
        download_dir = tmp_path / "downloads"
        download_dir.mkdir()
        current_file = download_dir / "TestApp_0.9_x86_64.AppImage.current"
        current_file.touch()

        parser = DummyVersionParser(filename_version="0.9", normalized="0.9-normalized")
        info_service = DummyInfoFileService(None, None)

        svc = LocalVersionService(version_parser=parser, info_service=info_service)
        app_config = SimpleNamespace(download_dir=download_dir)

        result = svc.get_current_version(app_config)  # type: ignore[arg-type]

        # _get_version_from_current_file returns the version extracted from
        # the filename without applying normalize_version_string.
        assert result == "0.9"

    def test_get_current_version_uses_file_analysis_as_fallback(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        download_dir = tmp_path / "downloads"
        download_dir.mkdir()
        app_file = download_dir / "TestApp_1.0_x86_64.AppImage"
        app_file.touch()

        parser = DummyVersionParser()
        info_service = DummyInfoFileService(None, None)

        svc = LocalVersionService(version_parser=parser, info_service=info_service)
        app_config = SimpleNamespace(download_dir=download_dir)

        monkeypatch.setattr(
            "appimage_updater.core.local_version_service.extract_versions_from_files",
            lambda files, extractor: [("1.0", app_file.stat().st_mtime, app_file)],
        )
        monkeypatch.setattr(
            "appimage_updater.core.local_version_service.select_newest_version",
            lambda version_files, normalizer: "1.0-final",
        )

        result = svc.get_current_version(app_config)  # type: ignore[arg-type]

        assert result == "1.0-final"

    def test_get_current_version_returns_none_when_no_sources(self, tmp_path: Path) -> None:
        download_dir = tmp_path / "empty"
        # Do not create the directory so service should treat as missing
        parser = DummyVersionParser()
        info_service = DummyInfoFileService(None, None)

        svc = LocalVersionService(version_parser=parser, info_service=info_service)
        app_config = SimpleNamespace(download_dir=download_dir)

        result = svc.get_current_version(app_config)  # type: ignore[arg-type]

        assert result is None
