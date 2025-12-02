import asyncio
import re
from typing import Any

import pytest

from appimage_updater.core import pattern_generator as pg


class FakeAsset:
    def __init__(self, name: str) -> None:
        self.name = name


class FakeRelease:
    def __init__(self, assets: list[FakeAsset], is_prerelease: bool = False, is_draft: bool = False) -> None:
        self.assets = assets
        self.is_prerelease = is_prerelease
        self.is_draft = is_draft


@pytest.mark.parametrize(
    ("url", "expected", "corrected"),
    [
        (
            "https://github.com/owner/repo/releases/download/v1.0/file.AppImage",
            "https://github.com/owner/repo",
            True,
        ),
        (
            "https://github.com/owner/repo/tree/main",
            "https://github.com/owner/repo",
            True,
        ),
        ("https://github.com/owner/repo", "https://github.com/owner/repo", False),
        ("https://example.com/owner/repo/releases/download/v1/file.AppImage", "https://example.com/owner/repo/releases/download/v1/file.AppImage", False),
    ],
)
def test_normalize_github_url(url: str, expected: str, corrected: bool) -> None:
    result, was_corrected = pg.normalize_github_url(url)

    assert result == expected
    assert was_corrected is corrected


def test_strip_extensions_list_mixed_case() -> None:
    filenames = ["App-1.0.AppImage", "App-1.1.appimage", "App-1.2.ZIP", "App-1.3.zip"]

    result = pg._strip_extensions_list(filenames)

    assert result == ["App-1.0", "App-1.1", "App-1.2", "App-1.3"]


@pytest.mark.parametrize(
    ("strings", "expected"),
    [
        ([], ""),
        (["MyApp", "MyAppPro"], "MyApp"),
    ],
)
def test_find_common_prefix(strings: list[str], expected: str) -> None:
    assert pg.find_common_prefix(strings) == expected


@pytest.mark.parametrize(
    ("prefix", "expected"),
    [
        ("MyApp-1.2.3-2025.09.10-x86_64", "MyApp"),
        ("Tool-conda-Linux-x86_64", "Tool"),
    ],
)
def test_generalize_pattern_prefix_removes_version_and_platform(prefix: str, expected: str) -> None:
    result = pg._generalize_pattern_prefix(prefix)

    # Result should start with the expected base name and no longer contain
    # obvious version, date, or platform markers.
    assert result.startswith(expected)
    assert "2025" not in result
    assert "x86_64" not in result
    assert "Linux" not in result
    assert "conda" not in result


def test_select_target_files_prefers_stable_app_over_others() -> None:
    releases = [
        FakeRelease(
            [
                FakeAsset("MyApp-1.0-x86_64.AppImage"),
                FakeAsset("MyApp-1.0.zip"),
            ],
            is_prerelease=False,
        ),
        FakeRelease(
            [FakeAsset("MyApp-1.1-x86_64.AppImage")],
            is_prerelease=True,
        ),
    ]

    groups = pg._collect_release_files(releases)  # type: ignore[arg-type]
    targets = pg._select_target_files(groups)

    assert targets is not None
    assert all(name.endswith(".AppImage") for name in targets)


def test_generate_appimage_pattern_async_uses_version_service_first(monkeypatch: Any) -> None:
    calls: dict[str, int] = {"vs": 0, "legacy": 0}

    async def fake_generate_pattern_from_repository(config: Any) -> str | None:  # noqa: ARG001
        calls["vs"] += 1
        return "PATTERN"

    async def fake_legacy_fetch_pattern(url: str) -> str | None:  # noqa: ARG001
        calls["legacy"] += 1
        return "LEGACY"

    monkeypatch.setattr(pg.version_service, "generate_pattern_from_repository", fake_generate_pattern_from_repository)
    monkeypatch.setattr(pg, "_legacy_fetch_pattern", fake_legacy_fetch_pattern)

    async def runner() -> None:
        result = await pg.generate_appimage_pattern_async("MyApp", "https://example.com/repo")

        # Pattern should come from version service and legacy path should not be used
        assert result is not None
        assert calls["vs"] == 1
        assert calls["legacy"] == 0

    asyncio.run(runner())


def test_generate_appimage_pattern_async_falls_back_to_legacy(monkeypatch: Any) -> None:
    calls: dict[str, int] = {"vs": 0, "legacy": 0}

    async def fake_generate_pattern_from_repository(config: Any) -> str | None:  # noqa: ARG001
        calls["vs"] += 1
        return None

    async def fake_legacy_fetch_pattern(url: str) -> str | None:  # noqa: ARG001
        calls["legacy"] += 1
        return "LEGACY"

    monkeypatch.setattr(pg.version_service, "generate_pattern_from_repository", fake_generate_pattern_from_repository)
    monkeypatch.setattr(pg, "_legacy_fetch_pattern", fake_legacy_fetch_pattern)

    async def runner() -> None:
        result = await pg.generate_appimage_pattern_async("MyApp", "https://example.com/repo")

        # When repository pattern generation fails, legacy path should be used
        assert result is not None
        assert calls["vs"] == 1
        assert calls["legacy"] == 1

    asyncio.run(runner())


def test_generate_appimage_pattern_async_handles_exception(monkeypatch: Any) -> None:
    async def fake_generate_pattern_from_repository(config: Any) -> str | None:  # noqa: ARG001
        raise RuntimeError("boom")

    monkeypatch.setattr(pg.version_service, "generate_pattern_from_repository", fake_generate_pattern_from_repository)

    async def runner() -> None:
        result = await pg.generate_appimage_pattern_async("MyApp", "https://example.com/repo")

        assert result is None

    asyncio.run(runner())


def test_should_enable_prerelease_true_when_only_prereleases(monkeypatch: Any) -> None:
    releases = [
        FakeRelease([FakeAsset("MyApp-1.0-x86_64.AppImage")], is_prerelease=True, is_draft=False),
        FakeRelease([FakeAsset("MyApp-1.1-x86_64.AppImage")], is_prerelease=True, is_draft=False),
    ]

    async def fake_fetch(url: str) -> list[FakeRelease]:  # noqa: ARG001
        return releases

    monkeypatch.setattr(pg, "_fetch_releases_for_prerelease_check", fake_fetch)

    async def runner() -> None:
        result = await pg.should_enable_prerelease("https://example.com/repo")

        assert result is True

    asyncio.run(runner())


def test_should_enable_prerelease_false_on_error(monkeypatch: Any) -> None:
    async def fake_fetch(url: str) -> list[FakeRelease]:  # noqa: ARG001
        raise pg.RepositoryError("failed")

    monkeypatch.setattr(pg, "_fetch_releases_for_prerelease_check", fake_fetch)

    async def runner() -> None:
        result = await pg.should_enable_prerelease("https://example.com/repo")

        assert result is False

    asyncio.run(runner())
