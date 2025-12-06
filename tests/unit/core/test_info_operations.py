import asyncio
import os
from pathlib import Path
import time
from typing import Any

import pytest

from appimage_updater.config.models import ApplicationConfig, ChecksumConfig
from appimage_updater.core import info_operations as io
from appimage_updater.repositories.base import RepositoryError


class DummyAsset:
    def __init__(self, name: str) -> None:
        self.name = name


class DummyRelease:
    def __init__(self, tag_name: str, asset_names: list[str]) -> None:
        self.tag_name = tag_name
        self.assets = [DummyAsset(n) for n in asset_names]


class DummyFormatter:
    def __init__(self) -> None:
        self.started_sections: list[str] = []
        self.messages: list[str] = []
        self.errors: list[str] = []
        self.successes: list[str] = []
        self.ended_sections: int = 0

    def start_section(self, name: str) -> None:
        self.started_sections.append(name)

    def print_message(self, msg: str) -> None:
        self.messages.append(msg)

    def print_error(self, msg: str) -> None:
        self.errors.append(msg)

    def print_success(self, msg: str) -> None:
        self.successes.append(msg)

    def end_section(self) -> None:
        self.ended_sections += 1


@pytest.fixture
def app_config(tmp_path: Path) -> ApplicationConfig:
    return ApplicationConfig(
        name="TestApp",
        source_type="github",
        url="https://github.com/test/testapp",
        download_dir=tmp_path,
        pattern=r"TestApp.*\\.AppImage$",
        enabled=True,
        rotation_enabled=False,
        checksum=ChecksumConfig(),
    )


def test_find_current_appimage_file_prefers_current_suffix(tmp_path: Path, app_config: ApplicationConfig) -> None:
    download_dir = tmp_path
    # A .current file should be preferred
    current = download_dir / "TestApp-1.0.AppImage.current"
    current.touch()
    regular = download_dir / "TestApp-1.0.AppImage"
    regular.touch()

    result = io._find_current_appimage_file(app_config, download_dir)

    assert result == current


def test_find_current_appimage_file_uses_latest_mtime(tmp_path: Path, app_config: ApplicationConfig) -> None:
    download_dir = tmp_path
    older = download_dir / "TestApp-0.9.AppImage"
    newer = download_dir / "TestApp-1.0.AppImage"
    older.touch()
    newer.touch()

    # Explicitly set different modification times to ensure reliable ordering
    # (files created in quick succession may have identical mtime in CI)
    now = time.time()
    os.utime(older, (now - 10, now - 10))  # 10 seconds older
    os.utime(newer, (now, now))  # current time

    result = io._find_current_appimage_file(app_config, download_dir)

    assert result == newer


def test_write_info_file_writes_expected_format(tmp_path: Path) -> None:
    info_file = tmp_path / "TestApp.info"

    io._write_info_file(info_file, "1.2.3")

    assert info_file.read_text() == "Version: 1.2.3\n"


@pytest.mark.parametrize(
    ("current", "asset", "expected"),
    [
        ("App-1.0.AppImage.current", "App-1.0.AppImage", True),
        ("App-1.0.AppImage.current", "App", True),
        ("App.AppImage.current", "App-1.0.AppImage", True),
        ("Other.AppImage.current", "App-1.0.AppImage", False),
    ],
)
def test_files_match(current: str, asset: str, expected: bool) -> None:
    assert io._files_match(current, asset) is expected


def test_find_matching_release_version_checks_assets() -> None:
    current = Path("TestApp-1.0.AppImage.current")
    releases = [
        DummyRelease("v0.9.0", ["Other-0.9.AppImage"]),
        DummyRelease("v1.0.0", ["TestApp-1.0.AppImage"]),
    ]

    result = io._find_matching_release_version(releases, current)

    assert result == "1.0.0"  # leading v is stripped in _check_release_assets


def test_extract_version_from_current_file_uses_repository_first(
    monkeypatch: Any,
    app_config: ApplicationConfig,
    tmp_path: Path,
) -> None:
    current_file = tmp_path / "TestApp-2.0.AppImage.current"
    current_file.touch()

    async def fake_get_version_from_repository(config: ApplicationConfig, _cf: Path) -> str | None:  # noqa: ARG001
        assert config is app_config
        return "v2.0.0"

    monkeypatch.setattr(io, "_get_version_from_repository", fake_get_version_from_repository)

    async def runner() -> None:
        result = await io._extract_version_from_current_file(app_config, current_file)

        # normalize_version_string should remove leading "v"
        assert result == "2.0.0"

    asyncio.run(runner())


def test_extract_version_from_current_file_falls_back_to_filename(
    monkeypatch: Any,
    app_config: ApplicationConfig,
    tmp_path: Path,
) -> None:
    current_file = tmp_path / "TestApp-3.1.AppImage.current"
    current_file.touch()

    async def fake_get_version_from_repository(config: ApplicationConfig, _cf: Path) -> str | None:  # noqa: ARG001
        return None

    def fake_extract_version_from_filename(filename: str, app_name: str) -> str | None:  # noqa: ARG001
        # Ensure we are called with the current file name
        assert filename == current_file.name
        return "3.1"

    monkeypatch.setattr(io, "_get_version_from_repository", fake_get_version_from_repository)
    monkeypatch.setattr(io, "extract_version_from_filename", fake_extract_version_from_filename)

    async def runner() -> None:
        result = await io._extract_version_from_current_file(app_config, current_file)

        assert result == "3.1"

    asyncio.run(runner())


def test_get_version_from_repository_returns_matching_version(
    monkeypatch: Any,
    app_config: ApplicationConfig,
    tmp_path: Path,
) -> None:
    current_file = tmp_path / "TestApp-1.0.AppImage.current"
    current_file.touch()

    class FakeClient:
        async def get_releases(self, url: str, limit: int) -> list[DummyRelease]:  # noqa: ARG002
            assert url == app_config.url
            return [DummyRelease("v1.0.0", ["TestApp-1.0.AppImage"])]

    async def fake_get_client(url: str) -> FakeClient:  # noqa: ARG001
        return FakeClient()

    monkeypatch.setattr(io, "_get_repository_client", fake_get_client)

    async def runner() -> None:
        result = await io._get_version_from_repository(app_config, current_file)

        assert result == "1.0.0"

    asyncio.run(runner())


def test_get_version_from_repository_handles_errors(
    monkeypatch: Any,
    app_config: ApplicationConfig,
    tmp_path: Path,
) -> None:
    current_file = tmp_path / "TestApp-1.0.AppImage.current"
    current_file.touch()

    async def fake_get_client(url: str):  # noqa: ANN001, ARG001
        raise RepositoryError("failed")

    monkeypatch.setattr(io, "_get_repository_client", fake_get_client)

    async def runner() -> None:
        result = await io._get_version_from_repository(app_config, current_file)

        assert result is None

    asyncio.run(runner())


def test_execute_info_update_workflow_invokes_per_app(
    monkeypatch: Any,
    app_config: ApplicationConfig,
) -> None:
    formatter = DummyFormatter()

    async def fake_process_single(app: ApplicationConfig, console: Any, output: DummyFormatter) -> None:  # noqa: ARG002
        assert app is app_config
        assert output is formatter

    def fake_get_output_formatter() -> DummyFormatter:
        return formatter

    # Patch formatter and per-app processor
    monkeypatch.setattr(io, "get_output_formatter", fake_get_output_formatter)
    monkeypatch.setattr(io, "_process_single_app_info_update", fake_process_single)

    async def runner() -> None:
        await io._execute_info_update_workflow([app_config])

        assert formatter.started_sections == ["Info File Update"]
        assert any("Updating .info files for" in msg for msg in formatter.messages)
        assert formatter.ended_sections == 1

    asyncio.run(runner())


def test_process_single_app_info_update_handles_error(monkeypatch: Any, app_config: ApplicationConfig) -> None:
    formatter = DummyFormatter()
    errors: list[str] = []

    async def failing_update(app: ApplicationConfig, console: Any) -> None:  # noqa: ARG002
        raise RepositoryError("boom")

    def fake_display(app_name: str, error_msg: str, output_formatter: DummyFormatter, console: Any) -> None:  # noqa: ARG001
        errors.append(f"{app_name}: {error_msg}")

    monkeypatch.setattr(io, "_update_info_file_for_app", failing_update)
    monkeypatch.setattr(io, "_display_app_error", fake_display)

    async def runner() -> None:
        await io._process_single_app_info_update(app_config, console=object(), output_formatter=formatter)

        assert errors
        assert errors[0].startswith("TestApp: ")

    asyncio.run(runner())
