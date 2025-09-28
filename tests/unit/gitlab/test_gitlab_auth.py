"""Tests for GitLab authentication module."""

import os
from unittest.mock import patch

import pytest

from appimage_updater.gitlab.auth import GitLabAuth


class TestGitLabAuth:
    """Test GitLab authentication functionality."""

    def test_init_with_explicit_token(self):
        """Test initialization with explicit token."""
        auth = GitLabAuth(token="test-token")
        assert auth.is_authenticated()
        assert auth.get_token() == "test-token"

    def test_init_without_token(self):
        """Test initialization without token."""
        with patch.dict(os.environ, {}, clear=True):
            auth = GitLabAuth()
            assert not auth.is_authenticated()
            assert auth.get_token() is None

    def test_init_with_gitlab_token_env(self):
        """Test initialization with GITLAB_TOKEN environment variable."""
        with patch.dict(os.environ, {"GITLAB_TOKEN": "env-token"}):
            auth = GitLabAuth()
            assert auth.is_authenticated()
            assert auth.get_token() == "env-token"

    def test_init_with_gitlab_private_token_env(self):
        """Test initialization with GITLAB_PRIVATE_TOKEN environment variable."""
        with patch.dict(os.environ, {"GITLAB_PRIVATE_TOKEN": "private-token"}):
            auth = GitLabAuth()
            assert auth.is_authenticated()
            assert auth.get_token() == "private-token"

    def test_env_token_priority(self):
        """Test that GITLAB_TOKEN takes priority over GITLAB_PRIVATE_TOKEN."""
        with patch.dict(os.environ, {
            "GITLAB_TOKEN": "primary-token",
            "GITLAB_PRIVATE_TOKEN": "secondary-token"
        }):
            auth = GitLabAuth()
            assert auth.get_token() == "primary-token"

    def test_get_headers_authenticated(self):
        """Test header generation when authenticated."""
        auth = GitLabAuth(token="test-token")
        headers = auth.get_headers()
        assert headers == {"PRIVATE-TOKEN": "test-token"}

    def test_get_headers_not_authenticated(self):
        """Test header generation when not authenticated."""
        with patch.dict(os.environ, {}, clear=True):
            auth = GitLabAuth()
            headers = auth.get_headers()
            assert headers == {}

    def test_set_token(self):
        """Test token update functionality."""
        auth = GitLabAuth()
        assert not auth.is_authenticated()
        
        auth.set_token("new-token")
        assert auth.is_authenticated()
        assert auth.get_token() == "new-token"
        
        auth.set_token(None)
        assert not auth.is_authenticated()
        assert auth.get_token() is None

    def test_get_auth_info_authenticated(self):
        """Test auth info when authenticated."""
        auth = GitLabAuth(token="test-token")
        info = auth.get_auth_info()
        
        assert info["authenticated"] is True
        assert info["token_source"] == "explicit"
        assert info["token_length"] == len("test-token")

    def test_get_auth_info_not_authenticated(self):
        """Test auth info when not authenticated."""
        with patch.dict(os.environ, {}, clear=True):
            auth = GitLabAuth()
            info = auth.get_auth_info()
            
            assert info["authenticated"] is False
            assert info["token_source"] is None
            assert info["token_length"] == 0

    def test_repr(self):
        """Test string representation."""
        auth_with_token = GitLabAuth(token="test-token")
        auth_without_token = GitLabAuth()
        
        assert "authenticated" in str(auth_with_token)
        assert "not authenticated" in str(auth_without_token)
