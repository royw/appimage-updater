"""Tests for distribution detection utilities."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest

from appimage_updater.dist_selector.detection_utilities import (
    _detect_current_distribution,
    _extract_distribution_info_from_os_release,
    _parse_fedora_issue,
    _parse_issue_content,
    _parse_issue_file,
    _parse_lsb_release,
    _parse_os_release,
    _parse_os_release_content,
    _parse_ubuntu_issue,
    _parse_version_number,
)
from appimage_updater.dist_selector.models import DistributionInfo


class TestParseVersionNumber:
    """Test version number parsing."""

    def test_parse_version_with_decimal(self) -> None:
        """Test parsing version with decimal."""
        assert _parse_version_number("24.04") == 24.04
        assert _parse_version_number("22.04") == 22.04
        assert _parse_version_number("11.4") == 11.4

    def test_parse_version_integer(self) -> None:
        """Test parsing integer version."""
        assert _parse_version_number("38") == 38.0
        assert _parse_version_number("39") == 39.0
        assert _parse_version_number("11") == 11.0

    def test_parse_version_invalid(self) -> None:
        """Test parsing invalid version strings."""
        assert _parse_version_number("invalid") == 0.0
        assert _parse_version_number("") == 0.0
        assert _parse_version_number("x.y") == 0.0

    def test_parse_version_edge_cases(self) -> None:
        """Test edge cases in version parsing."""
        assert _parse_version_number("0.0") == 0.0
        assert _parse_version_number("1") == 1.0
        assert _parse_version_number("99.99") == 99.99


class TestParseOsReleaseContent:
    """Test os-release content parsing."""

    def test_parse_basic_content(self) -> None:
        """Test parsing basic os-release content."""
        content = '''ID=ubuntu
VERSION_ID="24.04"
VERSION_CODENAME=noble
NAME="Ubuntu"'''
        
        result = _parse_os_release_content(content)
        
        assert result == {
            "ID": "ubuntu",
            "VERSION_ID": "24.04",
            "VERSION_CODENAME": "noble",
            "NAME": "Ubuntu"
        }

    def test_parse_with_quotes(self) -> None:
        """Test parsing content with various quote styles."""
        content = '''ID=fedora
VERSION_ID='38'
NAME="Fedora Linux"
VERSION_CODENAME='''
        
        result = _parse_os_release_content(content)
        
        assert result == {
            "ID": "fedora",
            "VERSION_ID": "38",
            "NAME": "Fedora Linux",
            "VERSION_CODENAME": ""
        }

    def test_parse_with_comments(self) -> None:
        """Test parsing content with comments."""
        content = '''# This is a comment
ID=ubuntu
# Another comment
VERSION_ID="24.04"'''
        
        result = _parse_os_release_content(content)
        
        assert result == {
            "ID": "ubuntu",
            "VERSION_ID": "24.04"
        }

    def test_parse_empty_content(self) -> None:
        """Test parsing empty content."""
        result = _parse_os_release_content("")
        assert result == {}

    def test_parse_malformed_lines(self) -> None:
        """Test parsing content with malformed lines."""
        content = '''ID=ubuntu
INVALID_LINE_WITHOUT_EQUALS
VERSION_ID="24.04"
=INVALID_EMPTY_KEY'''
        
        result = _parse_os_release_content(content)
        
        assert result == {
            "ID": "ubuntu",
            "VERSION_ID": "24.04",
            "": "INVALID_EMPTY_KEY"
        }


class TestExtractDistributionInfoFromOsRelease:
    """Test distribution info extraction from os-release data."""

    def test_extract_ubuntu_info(self) -> None:
        """Test extracting Ubuntu distribution info."""
        info = {
            "ID": "ubuntu",
            "VERSION_ID": "24.04",
            "VERSION_CODENAME": "noble"
        }
        
        result = _extract_distribution_info_from_os_release(info)
        
        assert result is not None
        assert result.id == "ubuntu"
        assert result.version == "24.04"
        assert result.version_numeric == 24.04
        assert result.codename == "noble"

    def test_extract_fedora_info(self) -> None:
        """Test extracting Fedora distribution info."""
        info = {
            "ID": "fedora",
            "VERSION_ID": "38"
        }
        
        result = _extract_distribution_info_from_os_release(info)
        
        assert result is not None
        assert result.id == "fedora"
        assert result.version == "38"
        assert result.version_numeric == 38.0
        assert result.codename is None

    def test_extract_missing_id(self) -> None:
        """Test extraction with missing ID."""
        info = {
            "VERSION_ID": "24.04"
        }
        
        result = _extract_distribution_info_from_os_release(info)
        
        assert result is None

    def test_extract_empty_id(self) -> None:
        """Test extraction with empty ID."""
        info = {
            "ID": "",
            "VERSION_ID": "24.04"
        }
        
        result = _extract_distribution_info_from_os_release(info)
        
        assert result is None

    def test_extract_missing_version(self) -> None:
        """Test extraction with missing version."""
        info = {
            "ID": "ubuntu"
        }
        
        result = _extract_distribution_info_from_os_release(info)
        
        assert result is not None
        assert result.id == "ubuntu"
        assert result.version == ""
        assert result.version_numeric == 0.0
        assert result.codename is None

    def test_extract_case_conversion(self) -> None:
        """Test that ID is converted to lowercase."""
        info = {
            "ID": "UBUNTU",
            "VERSION_ID": "24.04"
        }
        
        result = _extract_distribution_info_from_os_release(info)
        
        assert result is not None
        assert result.id == "ubuntu"


class TestParseOsRelease:
    """Test os-release file parsing."""

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_parse_successful(self, mock_read_text: Mock, mock_exists: Mock) -> None:
        """Test successful os-release parsing."""
        mock_exists.return_value = True
        mock_read_text.return_value = '''ID=ubuntu
VERSION_ID="24.04"
VERSION_CODENAME=noble'''
        
        result = _parse_os_release()
        
        assert result is not None
        assert result.id == "ubuntu"
        assert result.version == "24.04"
        assert result.codename == "noble"

    @patch('pathlib.Path.exists')
    def test_parse_file_not_exists(self, mock_exists: Mock) -> None:
        """Test parsing when file doesn't exist."""
        mock_exists.return_value = False
        
        result = _parse_os_release()
        
        assert result is None

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_parse_read_error(self, mock_read_text: Mock, mock_exists: Mock) -> None:
        """Test parsing with read error."""
        mock_exists.return_value = True
        mock_read_text.side_effect = OSError("Permission denied")
        
        result = _parse_os_release()
        
        assert result is None

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_parse_invalid_content(self, mock_read_text: Mock, mock_exists: Mock) -> None:
        """Test parsing with invalid content."""
        mock_exists.return_value = True
        mock_read_text.return_value = "INVALID_CONTENT_NO_ID"
        
        result = _parse_os_release()
        
        assert result is None


class TestParseLsbRelease:
    """Test lsb_release command parsing."""

    @patch('subprocess.run')
    def test_parse_ubuntu_successful(self, mock_run: Mock) -> None:
        """Test successful Ubuntu lsb_release parsing."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Description:\tUbuntu 24.04 LTS\n"
        mock_run.return_value = mock_result
        
        result = _parse_lsb_release()
        
        assert result is not None
        assert result.id == "ubuntu"
        assert result.version == "24.04"
        assert result.version_numeric == 24.04

    @patch('subprocess.run')
    def test_parse_non_ubuntu(self, mock_run: Mock) -> None:
        """Test parsing non-Ubuntu distribution."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Description:\tFedora Linux 38\n"
        mock_run.return_value = mock_result
        
        result = _parse_lsb_release()
        
        assert result is None

    @patch('subprocess.run')
    def test_parse_command_failed(self, mock_run: Mock) -> None:
        """Test parsing when command fails."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        result = _parse_lsb_release()
        
        assert result is None

    @patch('subprocess.run')
    def test_parse_timeout(self, mock_run: Mock) -> None:
        """Test parsing with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("lsb_release", 5)
        
        result = _parse_lsb_release()
        
        assert result is None

    @patch('subprocess.run')
    def test_parse_file_not_found(self, mock_run: Mock) -> None:
        """Test parsing when lsb_release not found."""
        mock_run.side_effect = FileNotFoundError()
        
        result = _parse_lsb_release()
        
        assert result is None

    @patch('subprocess.run')
    def test_parse_no_version_match(self, mock_run: Mock) -> None:
        """Test parsing Ubuntu without version match."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Description:\tUbuntu LTS\n"
        mock_run.return_value = mock_result
        
        result = _parse_lsb_release()
        
        assert result is None


class TestParseIssueFile:
    """Test issue file parsing."""

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_parse_ubuntu_successful(self, mock_read_text: Mock, mock_exists: Mock) -> None:
        """Test successful Ubuntu issue file parsing."""
        mock_exists.return_value = True
        mock_read_text.return_value = "Ubuntu 24.04 LTS \\n \\l\n"
        
        result = _parse_issue_file()
        
        assert result is not None
        assert result.id == "ubuntu"
        assert result.version == "24.04"
        assert result.version_numeric == 24.04

    @patch('pathlib.Path.exists')
    def test_parse_file_not_exists(self, mock_exists: Mock) -> None:
        """Test parsing when file doesn't exist."""
        mock_exists.return_value = False
        
        result = _parse_issue_file()
        
        assert result is None

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_parse_read_error(self, mock_read_text: Mock, mock_exists: Mock) -> None:
        """Test parsing with read error."""
        mock_exists.return_value = True
        mock_read_text.side_effect = OSError("Permission denied")
        
        result = _parse_issue_file()
        
        assert result is None


class TestParseIssueContent:
    """Test issue content parsing."""

    def test_parse_ubuntu_content(self) -> None:
        """Test parsing Ubuntu issue content."""
        content = "ubuntu 24.04 lts"
        
        result = _parse_issue_content(content)
        
        assert result is not None
        assert result.id == "ubuntu"
        assert result.version == "24.04"

    def test_parse_fedora_content(self) -> None:
        """Test parsing Fedora issue content."""
        content = "fedora linux 38"
        
        result = _parse_issue_content(content)
        
        assert result is not None
        assert result.id == "fedora"
        assert result.version == "38"

    def test_parse_unknown_content(self) -> None:
        """Test parsing unknown distribution content."""
        content = "some unknown linux distribution"
        
        result = _parse_issue_content(content)
        
        assert result is None


class TestParseUbuntuIssue:
    """Test Ubuntu issue parsing."""

    def test_parse_with_version(self) -> None:
        """Test parsing Ubuntu issue with version."""
        content = "ubuntu 24.04 lts"
        
        result = _parse_ubuntu_issue(content)
        
        assert result is not None
        assert result.id == "ubuntu"
        assert result.version == "24.04"
        assert result.version_numeric == 24.04

    def test_parse_without_version(self) -> None:
        """Test parsing Ubuntu issue without version."""
        content = "ubuntu lts"
        
        result = _parse_ubuntu_issue(content)
        
        assert result is None

    def test_parse_different_format(self) -> None:
        """Test parsing Ubuntu issue with different format."""
        content = "ubuntu 22.04.3 lts"
        
        result = _parse_ubuntu_issue(content)
        
        assert result is not None
        assert result.id == "ubuntu"
        assert result.version == "22.04"
        assert result.version_numeric == 22.04


class TestParseFedoraIssue:
    """Test Fedora issue parsing."""

    def test_parse_with_version(self) -> None:
        """Test parsing Fedora issue with version."""
        content = "fedora linux 38"
        
        result = _parse_fedora_issue(content)
        
        assert result is not None
        assert result.id == "fedora"
        assert result.version == "38"
        assert result.version_numeric == 38.0

    def test_parse_without_version(self) -> None:
        """Test parsing Fedora issue without version."""
        content = "fedora linux"
        
        result = _parse_fedora_issue(content)
        
        assert result is None

    def test_parse_different_format(self) -> None:
        """Test parsing Fedora issue with different format."""
        content = "fedora 39 workstation"
        
        result = _parse_fedora_issue(content)
        
        assert result is not None
        assert result.id == "fedora"
        assert result.version == "39"
        assert result.version_numeric == 39.0


class TestDetectCurrentDistribution:
    """Test current distribution detection."""

    @patch('appimage_updater.dist_selector.detection_utilities._parse_os_release')
    def test_detect_from_os_release(self, mock_parse_os_release: Mock) -> None:
        """Test detection from os-release."""
        expected = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)
        mock_parse_os_release.return_value = expected
        
        result = _detect_current_distribution()
        
        assert result == expected

    @patch('appimage_updater.dist_selector.detection_utilities._parse_os_release')
    @patch('appimage_updater.dist_selector.detection_utilities._parse_lsb_release')
    def test_detect_from_lsb_release(self, mock_parse_lsb: Mock, mock_parse_os: Mock) -> None:
        """Test detection from lsb_release when os-release fails."""
        mock_parse_os.return_value = None
        expected = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)
        mock_parse_lsb.return_value = expected
        
        result = _detect_current_distribution()
        
        assert result == expected

    @patch('appimage_updater.dist_selector.detection_utilities._parse_os_release')
    @patch('appimage_updater.dist_selector.detection_utilities._parse_lsb_release')
    @patch('appimage_updater.dist_selector.detection_utilities._parse_issue_file')
    def test_detect_from_issue_file(self, mock_parse_issue: Mock, mock_parse_lsb: Mock, mock_parse_os: Mock) -> None:
        """Test detection from issue file when other methods fail."""
        mock_parse_os.return_value = None
        mock_parse_lsb.return_value = None
        expected = DistributionInfo(id="ubuntu", version="24.04", version_numeric=24.04)
        mock_parse_issue.return_value = expected
        
        result = _detect_current_distribution()
        
        assert result == expected

    @patch('appimage_updater.dist_selector.detection_utilities._parse_os_release')
    @patch('appimage_updater.dist_selector.detection_utilities._parse_lsb_release')
    @patch('appimage_updater.dist_selector.detection_utilities._parse_issue_file')
    def test_detect_fallback_to_generic(self, mock_parse_issue: Mock, mock_parse_lsb: Mock, mock_parse_os: Mock) -> None:
        """Test fallback to generic Linux when all methods fail."""
        mock_parse_os.return_value = None
        mock_parse_lsb.return_value = None
        mock_parse_issue.return_value = None
        
        result = _detect_current_distribution()
        
        assert result.id == "linux"
        assert result.version == "unknown"
        assert result.version_numeric == 0.0
