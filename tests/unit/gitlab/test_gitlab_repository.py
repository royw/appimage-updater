"""Tests for GitLab repository implementation."""

from __future__ import annotations

import pytest

from appimage_updater.repositories.gitlab.repository import GitLabRepository


class TestGitLabRepository:
    """Test GitLab repository functionality."""

    def test_repository_type(self) -> None:
        """Test repository type identification."""
        repo = GitLabRepository()
        # repository_type property was removed, just test that repo can be created
        assert repo is not None

    def test_detect_repository_type_gitlab_com(self) -> None:
        """Test detection of gitlab.com URLs."""
        repo = GitLabRepository()

        # Test various gitlab.com URL formats
        assert repo.detect_repository_type("https://gitlab.com/owner/repo")
        assert repo.detect_repository_type("https://gitlab.com/group/subgroup/project")
        assert repo.detect_repository_type("https://www.gitlab.com/owner/repo")
        assert repo.detect_repository_type("http://gitlab.com/owner/repo")

    def test_detect_repository_type_self_hosted(self) -> None:
        """Test detection of self-hosted GitLab URLs."""
        repo = GitLabRepository()

        # Test self-hosted patterns
        assert repo.detect_repository_type("https://gitlab.example.com/owner/repo")
        assert repo.detect_repository_type("https://git.company.com/team/project")
        assert repo.detect_repository_type("https://example.com/gitlab/owner/repo")

    def test_detect_repository_type_non_gitlab(self) -> None:
        """Test rejection of non-GitLab URLs."""
        repo = GitLabRepository()

        # Test non-GitLab URLs
        assert not repo.detect_repository_type("https://github.com/owner/repo")
        assert not repo.detect_repository_type("https://bitbucket.org/owner/repo")
        assert not repo.detect_repository_type("https://example.com/owner/repo")

    def test_parse_repo_url_simple(self) -> None:
        """Test parsing simple GitLab URLs."""
        repo = GitLabRepository()

        owner, repo_name = repo.parse_repo_url("https://gitlab.com/owner/project")
        assert owner == "owner"
        assert repo_name == "project"

    def test_parse_repo_url_nested_groups(self) -> None:
        """Test parsing GitLab URLs with nested groups."""
        repo = GitLabRepository()

        owner, repo_name = repo.parse_repo_url("https://gitlab.com/group/subgroup/project")
        assert owner == "group/subgroup"
        assert repo_name == "project"

    def test_parse_repo_url_with_git_suffix(self) -> None:
        """Test parsing GitLab URLs with .git suffix."""
        repo = GitLabRepository()

        owner, repo_name = repo.parse_repo_url("https://gitlab.com/owner/project.git")
        assert owner == "owner"
        assert repo_name == "project"

    def test_parse_repo_url_invalid(self) -> None:
        """Test parsing invalid GitLab URLs."""
        repo = GitLabRepository()

        with pytest.raises(Exception):  # Should raise RepositoryError
            repo.parse_repo_url("https://gitlab.com/invalid")

        with pytest.raises(Exception):  # Should raise RepositoryError
            repo.parse_repo_url("invalid-url")

    def test_normalize_repo_url(self) -> None:
        """Test URL normalization."""
        repo = GitLabRepository()

        # Test .git suffix removal
        url, corrected = repo.normalize_repo_url("https://gitlab.com/owner/repo.git")
        assert url == "https://gitlab.com/owner/repo"
        assert corrected is True

        # Test trailing slash removal
        url, corrected = repo.normalize_repo_url("https://gitlab.com/owner/repo/")
        assert url == "https://gitlab.com/owner/repo"
        assert corrected is True

        # Test HTTP to HTTPS conversion
        url, corrected = repo.normalize_repo_url("http://gitlab.com/owner/repo")
        assert url == "https://gitlab.com/owner/repo"
        assert corrected is True

        # Test no changes needed
        url, corrected = repo.normalize_repo_url("https://gitlab.com/owner/repo")
        assert url == "https://gitlab.com/owner/repo"
        assert corrected is False

    def test_is_prerelease_detection(self) -> None:
        """Test prerelease detection logic."""
        repo = GitLabRepository()

        # Test prerelease patterns
        assert repo._is_prerelease("v1.0.0-alpha", "Alpha Release")
        assert repo._is_prerelease("v1.0.0-beta.1", "Beta Release")
        assert repo._is_prerelease("v1.0.0-rc.1", "Release Candidate")
        assert repo._is_prerelease("nightly-build", "Nightly Build")
        assert repo._is_prerelease("v1.0.0-dev", "Development Build")

        # Test stable releases
        assert not repo._is_prerelease("v1.0.0", "Stable Release")
        assert not repo._is_prerelease("1.2.3", "Version 1.2.3")
        assert not repo._is_prerelease("release-1.0", "Release 1.0")

    def test_generate_pattern_from_names(self) -> None:
        """Test pattern generation from asset names."""
        repo = GitLabRepository()

        # Test single AppImage
        pattern = repo._generate_pattern_from_names(["MyApp-v1.0.0.AppImage"])
        assert pattern is not None
        assert "MyApp" in pattern
        assert "AppImage" in pattern

        # Test multiple assets with common prefix
        pattern = repo._generate_pattern_from_names(
            ["MyApp-v1.0.0.AppImage", "MyApp-v1.1.0.AppImage", "MyApp-v2.0.0.AppImage"]
        )
        assert pattern is not None
        assert "MyApp" in pattern

        # Test no assets
        pattern = repo._generate_pattern_from_names([])
        assert pattern is None
