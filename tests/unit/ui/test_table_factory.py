"""Tests for the TableFactory utilities."""

from __future__ import annotations

from appimage_updater.ui.table_factory import TableFactory


class TestTableFactory:
    """Tests for TableFactory.create_applications_table."""

    def test_create_applications_table_structure(self) -> None:
        """Table should have expected title and column configuration."""
        table = TableFactory.create_applications_table()

        # Title
        assert table.title == "Configured Applications"

        # Column names
        column_names = [col.header for col in table.columns]
        assert column_names == [
            "Application",
            "Status",
            "Source",
            "Download Directory",
        ]

        # Column styles and flags
        assert table.columns[0].style == "cyan"
        assert table.columns[0].no_wrap is False

        assert table.columns[1].style == "green"

        assert table.columns[2].style == "yellow"
        # Overflow is stored on the column object in Rich
        assert str(table.columns[2].overflow) == "fold"

        assert table.columns[3].style == "magenta"
        assert table.columns[3].no_wrap is False
