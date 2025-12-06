"""Tests for GitHub repository prerelease detection with progressive fetching."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from appimage_updater.core.models import Asset, Release
from appimage_updater.repositories.github.repository import GitHubRepository


def make_release(version: str, is_prerelease: bool = False) -> Release:
    """Create a mock release for testing."""
    now = datetime.now()
    return Release(
        version=version,
        tag_name=version,
        published_at=now,
        assets=[
            Asset(
                name=f"App-{version}.AppImage",
                url=f"http://test.com/App-{version}.AppImage",
                size=1000,
                created_at=now,
            )
        ],
        is_prerelease=is_prerelease,
        is_draft=False,
    )


class TestShouldEnablePrereleaseProgressiveFetching:
    """Tests for progressive fetching in should_enable_prerelease."""

    @pytest.fixture
    def github_repo(self) -> GitHubRepository:
        return GitHubRepository()

    @pytest.mark.anyio
    async def test_finds_stable_release_in_first_batch(self, github_repo: GitHubRepository) -> None:
        """Test that stable release found in first 100 releases returns False."""
        releases = [make_release("v1.0.0", is_prerelease=False)]

        with patch.object(github_repo, "get_releases", new=AsyncMock(return_value=releases)) as mock:
            result = await github_repo.should_enable_prerelease("https://github.com/test/repo")

            assert result is False
            # Should only fetch once since stable was found
            mock.assert_called_once()

    @pytest.mark.anyio
    async def test_returns_true_when_all_prereleases_and_fewer_than_limit(
        self, github_repo: GitHubRepository
    ) -> None:
        """Test returns True when only prereleases and count < limit (all fetched)."""
        # 50 prereleases - fewer than 100, so we know we've fetched all
        releases = [make_release(f"v1.0.0-beta{i}", is_prerelease=True) for i in range(50)]

        with patch.object(github_repo, "get_releases", new=AsyncMock(return_value=releases)):
            result = await github_repo.should_enable_prerelease("https://github.com/test/repo")

            assert result is True

    @pytest.mark.anyio
    async def test_expands_search_when_limit_reached_without_stable(
        self, github_repo: GitHubRepository
    ) -> None:
        """Test that search expands when limit reached without finding stable."""
        # First call: 100 prereleases (exactly at limit, might be more)
        first_batch = [make_release(f"weekly-{i}", is_prerelease=True) for i in range(100)]
        # Second call: 150 releases including 1 stable (found stable, stop)
        second_batch = [make_release(f"weekly-{i}", is_prerelease=True) for i in range(149)]
        second_batch.append(make_release("v1.0.0", is_prerelease=False))

        call_count = 0

        async def mock_get_releases(url: str, limit: int = 100) -> list[Release]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                assert limit == 100
                return first_batch
            else:
                assert limit == 200  # Doubled
                return second_batch

        with patch.object(github_repo, "get_releases", side_effect=mock_get_releases):
            result = await github_repo.should_enable_prerelease("https://github.com/test/repo")

            assert result is False  # Found stable in second batch
            assert call_count == 2

    @pytest.mark.anyio
    async def test_stops_at_max_limit(self, github_repo: GitHubRepository) -> None:
        """Test that search stops at max limit (1600) even without stable."""
        # Always return exactly limit prereleases to trigger expansion
        async def mock_get_releases(url: str, limit: int = 100) -> list[Release]:
            return [make_release(f"weekly-{i}", is_prerelease=True) for i in range(limit)]

        with patch.object(github_repo, "get_releases", side_effect=mock_get_releases):
            result = await github_repo.should_enable_prerelease("https://github.com/test/repo")

            # Should return True (no stable found) and stop at max limit
            assert result is True

    @pytest.mark.anyio
    async def test_handles_empty_releases(self, github_repo: GitHubRepository) -> None:
        """Test returns False when no releases found."""
        with patch.object(github_repo, "get_releases", new=AsyncMock(return_value=[])):
            result = await github_repo.should_enable_prerelease("https://github.com/test/repo")

            assert result is False

    @pytest.mark.anyio
    async def test_filters_valid_releases(self, github_repo: GitHubRepository) -> None:
        """Test that releases without AppImage assets are filtered out."""
        # Release with no assets
        now = datetime.now()
        no_asset_release = Release(
            version="v1.0.0",
            tag_name="v1.0.0",
            published_at=now,
            assets=[],
            is_prerelease=False,
            is_draft=False,
        )
        # Only release with no assets
        releases = [no_asset_release]

        with patch.object(github_repo, "get_releases", new=AsyncMock(return_value=releases)):
            result = await github_repo.should_enable_prerelease("https://github.com/test/repo")

            # No valid releases, should return False
            assert result is False


class TestShouldEnablePrereleaseRealWorldScenarios:
    """Tests simulating real-world scenarios like FreeCAD."""

    @pytest.fixture
    def github_repo(self) -> GitHubRepository:
        return GitHubRepository()

    @pytest.mark.anyio
    async def test_freecad_scenario_stable_buried_under_weeklies(
        self, github_repo: GitHubRepository
    ) -> None:
        """Test FreeCAD-like scenario where stable is buried under many weekly builds."""
        # Simulate FreeCAD: ~25 weekly builds before 1 stable release

        async def mock_get_releases(url: str, limit: int = 100) -> list[Release]:
            releases = []
            # 25 weekly builds (all prereleases)
            for i in range(25):
                releases.append(make_release(f"weekly-2025.12.{i:02d}", is_prerelease=True))
            # Then a stable release
            releases.append(make_release("1.0.2", is_prerelease=False))
            return releases[:limit]

        with patch.object(github_repo, "get_releases", side_effect=mock_get_releases):
            result = await github_repo.should_enable_prerelease("https://github.com/FreeCAD/FreeCAD")

            # Should find the stable release and return False
            assert result is False

    @pytest.mark.anyio
    async def test_continuous_build_only_repo(self, github_repo: GitHubRepository) -> None:
        """Test repo that only has continuous/prerelease builds."""
        # All releases are prereleases, fewer than limit
        releases = [make_release(f"continuous-{i}", is_prerelease=True) for i in range(10)]

        with patch.object(github_repo, "get_releases", new=AsyncMock(return_value=releases)):
            result = await github_repo.should_enable_prerelease("https://github.com/test/continuous")

            assert result is True
