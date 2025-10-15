"""Tests for application service."""

from __future__ import annotations

from unittest.mock import Mock, patch

from appimage_updater.services.application_service import ApplicationService
from appimage_updater.ui.output.context import OutputFormatterContext
from appimage_updater.ui.output.rich_formatter import RichOutputFormatter


class MockApp:
    """Mock application for testing."""

    def __init__(self, name: str) -> None:
        self.name = name


class TestFilterAppsByNames:
    """Tests for filter_apps_by_names method."""

    def test_filter_empty_app_names(self) -> None:
        """Test filtering with empty app names returns all apps."""
        apps = [MockApp("App1"), MockApp("App2")]

        result = ApplicationService.filter_apps_by_names(apps, [])

        assert result == apps

    def test_filter_exact_match_single(self) -> None:
        """Test filtering with exact match for single app."""
        apps = [MockApp("App1"), MockApp("App2"), MockApp("App3")]

        result = ApplicationService.filter_apps_by_names(apps, ["App2"])

        assert result is not None
        assert len(result) == 1
        assert result[0].name == "App2"

    def test_filter_exact_match_case_insensitive(self) -> None:
        """Test filtering is case-insensitive."""
        apps = [MockApp("App1"), MockApp("App2")]

        result = ApplicationService.filter_apps_by_names(apps, ["app2"])

        assert result is not None
        assert len(result) == 1
        assert result[0].name == "App2"

    def test_filter_multiple_exact_matches(self) -> None:
        """Test filtering with multiple exact matches."""
        apps = [MockApp("App1"), MockApp("App2"), MockApp("App3")]

        result = ApplicationService.filter_apps_by_names(apps, ["App1", "App3"])

        assert result is not None
        assert len(result) == 2
        assert result[0].name == "App1"
        assert result[1].name == "App3"

    def test_filter_glob_pattern_wildcard(self) -> None:
        """Test filtering with glob pattern using wildcard."""
        apps = [MockApp("OrcaSlicer"), MockApp("OrcaSlicerRC"), MockApp("BambuStudio")]

        result = ApplicationService.filter_apps_by_names(apps, ["Orca*"])

        assert result is not None
        assert len(result) == 2
        assert result[0].name == "OrcaSlicer"
        assert result[1].name == "OrcaSlicerRC"

    def test_filter_glob_pattern_question_mark(self) -> None:
        """Test filtering with glob pattern using question mark."""
        apps = [MockApp("App1"), MockApp("App2"), MockApp("App10")]

        result = ApplicationService.filter_apps_by_names(apps, ["App?"])

        assert result is not None
        assert len(result) == 2
        assert result[0].name == "App1"
        assert result[1].name == "App2"

    def test_filter_not_found_returns_none(self) -> None:
        """Test filtering with non-existent app returns None."""
        apps = [MockApp("App1"), MockApp("App2")]
        formatter = RichOutputFormatter()

        with OutputFormatterContext(formatter):
            result = ApplicationService.filter_apps_by_names(apps, ["NonExistent"])

        assert result is None

    def test_filter_removes_duplicates(self) -> None:
        """Test filtering removes duplicate matches."""
        apps = [MockApp("App1"), MockApp("App2")]

        # Request same app twice
        result = ApplicationService.filter_apps_by_names(apps, ["App1", "App1"])

        assert result is not None
        assert len(result) == 1
        assert result[0].name == "App1"

    def test_filter_preserves_order(self) -> None:
        """Test filtering preserves order of first occurrence."""
        apps = [MockApp("App1"), MockApp("App2"), MockApp("App3")]

        result = ApplicationService.filter_apps_by_names(apps, ["App3", "App1", "App2"])

        assert result is not None
        assert len(result) == 3
        assert result[0].name == "App3"
        assert result[1].name == "App1"
        assert result[2].name == "App2"


class TestFilterAppsBySingleName:
    """Tests for _filter_apps_by_single_name method."""

    def test_exact_match_preferred_over_glob(self) -> None:
        """Test exact match is preferred over glob match."""
        apps = [MockApp("App"), MockApp("App1"), MockApp("App2")]

        result = ApplicationService._filter_apps_by_single_name(apps, "App")

        assert len(result) == 1
        assert result[0].name == "App"

    def test_glob_match_when_no_exact_match(self) -> None:
        """Test glob matching when no exact match exists."""
        apps = [MockApp("App1"), MockApp("App2"), MockApp("App3")]

        result = ApplicationService._filter_apps_by_single_name(apps, "App*")

        assert len(result) == 3

    def test_no_matches_returns_empty_list(self) -> None:
        """Test no matches returns empty list."""
        apps = [MockApp("App1"), MockApp("App2")]

        result = ApplicationService._filter_apps_by_single_name(apps, "NonExistent")

        assert result == []


class TestFindExactMatches:
    """Tests for _find_exact_matches method."""

    def test_find_exact_match(self) -> None:
        """Test finding exact match."""
        apps = [MockApp("App1"), MockApp("App2")]

        result = ApplicationService._find_exact_matches(apps, "app1")

        assert len(result) == 1
        assert result[0].name == "App1"

    def test_find_no_exact_match(self) -> None:
        """Test finding no exact match."""
        apps = [MockApp("App1"), MockApp("App2")]

        result = ApplicationService._find_exact_matches(apps, "app3")

        assert result == []

    def test_find_multiple_exact_matches(self) -> None:
        """Test finding multiple apps with same name."""
        apps = [MockApp("App"), MockApp("App"), MockApp("Other")]

        result = ApplicationService._find_exact_matches(apps, "app")

        assert len(result) == 2


class TestFindGlobMatches:
    """Tests for _find_glob_matches method."""

    def test_find_glob_matches_wildcard(self) -> None:
        """Test finding glob matches with wildcard."""
        apps = [MockApp("Test1"), MockApp("Test2"), MockApp("Other")]

        result = ApplicationService._find_glob_matches(apps, "test*")

        assert len(result) == 2

    def test_find_glob_matches_question_mark(self) -> None:
        """Test finding glob matches with question mark."""
        apps = [MockApp("A1"), MockApp("A2"), MockApp("A10")]

        result = ApplicationService._find_glob_matches(apps, "a?")

        assert len(result) == 2

    def test_find_glob_matches_character_class(self) -> None:
        """Test finding glob matches with character class."""
        apps = [MockApp("App1"), MockApp("App2"), MockApp("App3")]

        result = ApplicationService._find_glob_matches(apps, "app[12]")

        assert len(result) == 2


class TestCollectAppMatches:
    """Tests for _collect_app_matches method."""

    def test_collect_all_found(self) -> None:
        """Test collecting when all apps are found."""
        apps = [MockApp("App1"), MockApp("App2"), MockApp("App3")]

        matches, not_found = ApplicationService._collect_app_matches(apps, ["App1", "App2"])

        assert len(matches) == 2
        assert not_found == []

    def test_collect_some_not_found(self) -> None:
        """Test collecting when some apps are not found."""
        apps = [MockApp("App1"), MockApp("App2")]

        matches, not_found = ApplicationService._collect_app_matches(apps, ["App1", "NonExistent"])

        assert len(matches) == 1
        assert not_found == ["NonExistent"]

    def test_collect_all_not_found(self) -> None:
        """Test collecting when all apps are not found."""
        apps = [MockApp("App1"), MockApp("App2")]

        matches, not_found = ApplicationService._collect_app_matches(apps, ["NonExistent1", "NonExistent2"])

        assert matches == []
        assert not_found == ["NonExistent1", "NonExistent2"]


class TestProcessAppMatches:
    """Tests for _process_app_matches method."""

    def test_process_with_matches(self) -> None:
        """Test processing when matches exist."""
        all_matches: list[MockApp] = []
        not_found: list[str] = []
        matches = [MockApp("App1")]

        ApplicationService._process_app_matches(matches, "App1", all_matches, not_found)

        assert len(all_matches) == 1
        assert not_found == []

    def test_process_without_matches(self) -> None:
        """Test processing when no matches exist."""
        all_matches: list[MockApp] = []
        not_found: list[str] = []
        matches: list[MockApp] = []

        ApplicationService._process_app_matches(matches, "NonExistent", all_matches, not_found)

        assert all_matches == []
        assert not_found == ["NonExistent"]


class TestRemoveDuplicateApps:
    """Tests for _remove_duplicate_apps method."""

    def test_remove_duplicates_preserves_first(self) -> None:
        """Test removing duplicates preserves first occurrence."""
        apps = [MockApp("App1"), MockApp("App2"), MockApp("App1")]

        result = ApplicationService._remove_duplicate_apps(apps)

        assert len(result) == 2
        assert result[0].name == "App1"
        assert result[1].name == "App2"

    def test_remove_duplicates_no_duplicates(self) -> None:
        """Test removing duplicates when none exist."""
        apps = [MockApp("App1"), MockApp("App2"), MockApp("App3")]

        result = ApplicationService._remove_duplicate_apps(apps)

        assert len(result) == 3

    def test_remove_duplicates_all_same(self) -> None:
        """Test removing duplicates when all are same."""
        apps = [MockApp("App"), MockApp("App"), MockApp("App")]

        result = ApplicationService._remove_duplicate_apps(apps)

        assert len(result) == 1


class TestHandleAppsNotFound:
    """Tests for _handle_apps_not_found method."""

    def test_handle_with_formatter(self) -> None:
        """Test handling not found apps with formatter."""
        apps = [MockApp("App1"), MockApp("App2")]
        not_found = ["NonExistent"]

        mock_formatter = Mock()
        with patch("appimage_updater.services.application_service.get_output_formatter", return_value=mock_formatter):
            result = ApplicationService._handle_apps_not_found(not_found, apps)

            assert result is False
            mock_formatter.print_error.assert_called_once()
            mock_formatter.print_warning.assert_called_once()
            mock_formatter.print_info.assert_called()

    def test_handle_without_formatter(self) -> None:
        """Test handling not found apps - now always uses formatter."""
        apps = [MockApp("App1"), MockApp("App2")]
        not_found = ["NonExistent"]
        formatter = RichOutputFormatter()

        with OutputFormatterContext(formatter):
            result = ApplicationService._handle_apps_not_found(not_found, apps)

        assert result is False

    def test_handle_includes_available_apps(self) -> None:
        """Test handling includes available apps in message."""
        apps = [MockApp("App1"), MockApp("App2")]
        not_found = ["NonExistent"]

        mock_formatter = Mock()
        with patch("appimage_updater.services.application_service.get_output_formatter", return_value=mock_formatter):
            ApplicationService._handle_apps_not_found(not_found, apps)

            # Check that available apps are mentioned
            calls = mock_formatter.print_info.call_args_list
            assert any("App1" in str(call) and "App2" in str(call) for call in calls)


class TestPrintTroubleshootingTipsFormatted:
    """Tests for _print_troubleshooting_tips_formatted method."""

    def test_print_with_available_apps(self) -> None:
        """Test printing tips with available apps."""
        mock_formatter = Mock()
        available_apps = ["App1", "App2"]

        ApplicationService._print_troubleshooting_tips_formatted(mock_formatter, available_apps)

        assert mock_formatter.print_info.call_count == 4
        calls = [str(call) for call in mock_formatter.print_info.call_args_list]
        assert any("App1" in call and "App2" in call for call in calls)

    def test_print_without_available_apps(self) -> None:
        """Test printing tips without available apps."""
        mock_formatter = Mock()
        available_apps: list[str] = []

        ApplicationService._print_troubleshooting_tips_formatted(mock_formatter, available_apps)

        assert mock_formatter.print_info.call_count == 4
        calls = [str(call) for call in mock_formatter.print_info.call_args_list]
        assert any("None configured" in call for call in calls)


class TestIntegrationScenarios:
    """Integration tests for application service workflows."""

    def test_complex_filtering_workflow(self) -> None:
        """Test complex filtering with multiple patterns."""
        apps = [
            MockApp("OrcaSlicer"),
            MockApp("OrcaSlicerRC"),
            MockApp("OrcaSlicerNightly"),
            MockApp("BambuStudio"),
            MockApp("PrusaSlicer"),
        ]

        result = ApplicationService.filter_apps_by_names(apps, ["Orca*", "Bambu*"])

        assert result is not None
        assert len(result) == 4  # 3 Orca + 1 Bambu

    def test_mixed_exact_and_glob_patterns(self) -> None:
        """Test mixing exact matches and glob patterns."""
        apps = [MockApp("App1"), MockApp("App2"), MockApp("Test1"), MockApp("Test2")]

        result = ApplicationService.filter_apps_by_names(apps, ["App1", "Test*"])

        assert result is not None
        assert len(result) == 3  # App1 + Test1 + Test2

    def test_case_insensitive_glob_matching(self) -> None:
        """Test case-insensitive glob matching."""
        apps = [MockApp("UPPERCASE"), MockApp("lowercase"), MockApp("MixedCase")]

        result = ApplicationService.filter_apps_by_names(apps, ["*case"])

        assert result is not None
        assert len(result) == 3  # All match

    def test_error_handling_with_partial_matches(self) -> None:
        """Test error handling when some apps match and some don't."""
        apps = [MockApp("App1"), MockApp("App2")]
        formatter = RichOutputFormatter()

        with OutputFormatterContext(formatter):
            result = ApplicationService.filter_apps_by_names(apps, ["App1", "NonExistent"])

        assert result is None  # Error occurred
