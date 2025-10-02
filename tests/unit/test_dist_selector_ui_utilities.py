"""Unit tests for dist_selector.ui_utilities module."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock, patch

from appimage_updater.core.models import Asset
from appimage_updater.dist_selector.models import AssetInfo
from appimage_updater.dist_selector.ui_utilities import _prompt_user_selection


class TestPromptUserSelection:
    """Test cases for _prompt_user_selection function."""

    def test_prompt_user_selection_valid_choice_first(self) -> None:
        """Test selecting the first asset."""
        # Create test assets
        asset1 = Asset(
            name="app-ubuntu.AppImage", url="https://example.com/app1.AppImage", size=1024, created_at=datetime.now()
        )
        asset2 = Asset(
            name="app-fedora.AppImage", url="https://example.com/app2.AppImage", size=2048, created_at=datetime.now()
        )

        asset_infos = [
            AssetInfo(asset=asset1, distribution="ubuntu", version="24.04", score=90.0),
            AssetInfo(asset=asset2, distribution="fedora", version="38", score=85.0),
        ]

        mock_console = Mock()

        with patch("appimage_updater.dist_selector.ui_utilities.Prompt.ask", return_value="1"):
            result = _prompt_user_selection(asset_infos, mock_console)

        assert result == asset_infos[0]
        assert result.distribution == "ubuntu"

    def test_prompt_user_selection_valid_choice_second(self) -> None:
        """Test selecting the second asset."""
        asset1 = Asset(
            name="app-ubuntu.AppImage", url="https://example.com/app1.AppImage", size=1024, created_at=datetime.now()
        )
        asset2 = Asset(
            name="app-fedora.AppImage", url="https://example.com/app2.AppImage", size=2048, created_at=datetime.now()
        )

        asset_infos = [
            AssetInfo(asset=asset1, distribution="ubuntu", version="24.04", score=90.0),
            AssetInfo(asset=asset2, distribution="fedora", version="38", score=85.0),
        ]

        mock_console = Mock()

        with patch("appimage_updater.dist_selector.ui_utilities.Prompt.ask", return_value="2"):
            result = _prompt_user_selection(asset_infos, mock_console)

        assert result == asset_infos[1]
        assert result.distribution == "fedora"

    def test_prompt_user_selection_default_choice(self) -> None:
        """Test using default choice (empty input)."""
        asset = Asset(name="app.AppImage", url="https://example.com/app.AppImage", size=1024, created_at=datetime.now())

        asset_infos = [AssetInfo(asset=asset, distribution="ubuntu", score=90.0)]

        mock_console = Mock()

        with patch("appimage_updater.dist_selector.ui_utilities.Prompt.ask", return_value="1"):
            result = _prompt_user_selection(asset_infos, mock_console)

        assert result == asset_infos[0]

    def test_prompt_user_selection_invalid_then_valid(self) -> None:
        """Test invalid choice followed by valid choice."""
        asset = Asset(name="app.AppImage", url="https://example.com/app.AppImage", size=1024, created_at=datetime.now())

        asset_infos = [AssetInfo(asset=asset, distribution="ubuntu", score=90.0)]

        mock_console = Mock()

        with patch("appimage_updater.dist_selector.ui_utilities.Prompt.ask", side_effect=["5", "1"]):
            result = _prompt_user_selection(asset_infos, mock_console)

        assert result == asset_infos[0]
        # Should have printed error message for invalid choice
        mock_console.print.assert_any_call("[red]Please enter a number between 1 and 1[/red]")

    def test_prompt_user_selection_zero_invalid(self) -> None:
        """Test that zero is treated as invalid choice."""
        asset = Asset(name="app.AppImage", url="https://example.com/app.AppImage", size=1024, created_at=datetime.now())

        asset_infos = [AssetInfo(asset=asset, distribution="ubuntu", score=90.0)]

        mock_console = Mock()

        with patch("appimage_updater.dist_selector.ui_utilities.Prompt.ask", side_effect=["0", "1"]):
            result = _prompt_user_selection(asset_infos, mock_console)

        assert result == asset_infos[0]
        mock_console.print.assert_any_call("[red]Please enter a number between 1 and 1[/red]")

    def test_prompt_user_selection_negative_invalid(self) -> None:
        """Test that negative numbers are treated as invalid."""
        asset = Asset(name="app.AppImage", url="https://example.com/app.AppImage", size=1024, created_at=datetime.now())

        asset_infos = [AssetInfo(asset=asset, distribution="ubuntu", score=90.0)]

        mock_console = Mock()

        with patch("appimage_updater.dist_selector.ui_utilities.Prompt.ask", side_effect=["-1", "1"]):
            result = _prompt_user_selection(asset_infos, mock_console)

        assert result == asset_infos[0]
        mock_console.print.assert_any_call("[red]Please enter a number between 1 and 1[/red]")

    def test_prompt_user_selection_value_error_handling(self) -> None:
        """Test handling of non-numeric input."""
        asset = Asset(name="app.AppImage", url="https://example.com/app.AppImage", size=1024, created_at=datetime.now())

        asset_infos = [AssetInfo(asset=asset, distribution="ubuntu", score=90.0)]

        mock_console = Mock()

        with patch("appimage_updater.dist_selector.ui_utilities.Prompt.ask", side_effect=["abc", "1"]):
            result = _prompt_user_selection(asset_infos, mock_console)

        assert result == asset_infos[0]
        mock_console.print.assert_any_call("[red]Invalid selection. Please try again.[/red]")

    def test_prompt_user_selection_keyboard_interrupt_handling(self) -> None:
        """Test handling of KeyboardInterrupt (Ctrl+C)."""
        asset = Asset(name="app.AppImage", url="https://example.com/app.AppImage", size=1024, created_at=datetime.now())

        asset_infos = [AssetInfo(asset=asset, distribution="ubuntu", score=90.0)]

        mock_console = Mock()

        with patch("appimage_updater.dist_selector.ui_utilities.Prompt.ask", side_effect=[KeyboardInterrupt(), "1"]):
            result = _prompt_user_selection(asset_infos, mock_console)

        assert result == asset_infos[0]
        mock_console.print.assert_any_call("[red]Invalid selection. Please try again.[/red]")

    def test_prompt_user_selection_eof_error_handling(self) -> None:
        """Test handling of EOFError (non-interactive environment)."""
        asset1 = Asset(
            name="app-best.AppImage", url="https://example.com/app1.AppImage", size=1024, created_at=datetime.now()
        )
        asset2 = Asset(
            name="app-second.AppImage", url="https://example.com/app2.AppImage", size=2048, created_at=datetime.now()
        )

        asset_infos = [
            AssetInfo(asset=asset1, distribution="ubuntu", score=95.0),
            AssetInfo(asset=asset2, distribution="fedora", score=85.0),
        ]

        mock_console = Mock()

        with patch("appimage_updater.dist_selector.ui_utilities.Prompt.ask", side_effect=EOFError()):
            result = _prompt_user_selection(asset_infos, mock_console)

        # Should return the first (best) asset
        assert result == asset_infos[0]
        assert result.score == 95.0
        mock_console.print.assert_any_call("[yellow]Non-interactive environment detected, using best match[/yellow]")

    def test_prompt_user_selection_table_creation(self) -> None:
        """Test that table is created and displayed correctly."""
        asset1 = Asset(
            name="app-ubuntu-24.04-x86_64.AppImage",
            url="https://example.com/app1.AppImage",
            size=1024,
            created_at=datetime.now(),
        )
        asset2 = Asset(
            name="app-generic.AppImage", url="https://example.com/app2.AppImage", size=2048, created_at=datetime.now()
        )

        asset_infos = [
            AssetInfo(asset=asset1, distribution="ubuntu", version="24.04", arch="x86_64", score=92.5),
            AssetInfo(
                asset=asset2,
                distribution=None,  # Should show as "Generic"
                version=None,  # Should show as "Any"
                arch=None,  # Should show as "Any"
                score=75.0,
            ),
        ]

        mock_console = Mock()

        with (
            patch("appimage_updater.dist_selector.ui_utilities.Prompt.ask", return_value="1"),
            patch("appimage_updater.dist_selector.ui_utilities.Table") as mock_table_class,
        ):
            mock_table = Mock()
            mock_table_class.return_value = mock_table

            _prompt_user_selection(asset_infos, mock_console)

            # Verify table creation
            mock_table_class.assert_called_once_with(show_header=True, header_style="bold magenta")

            # Verify columns were added (6 columns total)
            assert mock_table.add_column.call_count == 6
            mock_table.add_column.assert_any_call("#", style="dim", width=3)
            mock_table.add_column.assert_any_call("Asset Name", style="cyan")
            mock_table.add_column.assert_any_call("Distribution", style="green")
            mock_table.add_column.assert_any_call("Version", style="yellow")
            mock_table.add_column.assert_any_call("Architecture", style="blue")
            mock_table.add_column.assert_any_call("Score", style="magenta", justify="right")

            # Verify rows were added
            assert mock_table.add_row.call_count == 2
            mock_table.add_row.assert_any_call(
                "1", "app-ubuntu-24.04-x86_64.AppImage", "ubuntu", "24.04", "x86_64", "92.5"
            )
            mock_table.add_row.assert_any_call("2", "app-generic.AppImage", "Generic", "Any", "Any", "75.0")

            # Verify table was printed
            mock_console.print.assert_any_call(mock_table)

    def test_prompt_user_selection_single_asset(self) -> None:
        """Test selection with only one asset."""
        asset = Asset(
            name="only-app.AppImage", url="https://example.com/app.AppImage", size=1024, created_at=datetime.now()
        )

        asset_infos = [AssetInfo(asset=asset, distribution="arch", version="rolling", score=100.0)]

        mock_console = Mock()

        with patch("appimage_updater.dist_selector.ui_utilities.Prompt.ask", return_value="1"):
            result = _prompt_user_selection(asset_infos, mock_console)

        assert result == asset_infos[0]
        assert result.distribution == "arch"

    def test_prompt_user_selection_multiple_retries(self) -> None:
        """Test multiple invalid attempts before valid selection."""
        asset = Asset(name="app.AppImage", url="https://example.com/app.AppImage", size=1024, created_at=datetime.now())

        asset_infos = [AssetInfo(asset=asset, distribution="ubuntu", score=90.0)]

        mock_console = Mock()

        with patch("appimage_updater.dist_selector.ui_utilities.Prompt.ask", side_effect=["abc", "0", "2", "1"]):
            result = _prompt_user_selection(asset_infos, mock_console)

        assert result == asset_infos[0]

        # Should have printed error messages for each invalid attempt
        error_calls = [call for call in mock_console.print.call_args_list if "[red]" in str(call)]
        assert len(error_calls) >= 3  # At least 3 error messages
