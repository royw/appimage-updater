"""Table factory for creating standardized Rich tables."""

from rich.table import Table


class TableFactory:
    """Factory for creating standardized Rich tables."""

    @staticmethod
    def create_applications_table(title: str = "Configured Applications") -> Table:
        """Create standard applications table.

        Args:
            title: Table title

        Returns:
            Configured Rich Table instance
        """
        table = Table(title=title)
        table.add_column("Application", style="cyan", no_wrap=False)
        table.add_column("Status", style="green")
        table.add_column("Source", style="yellow", no_wrap=False, overflow="fold")
        table.add_column("Download Directory", style="magenta", no_wrap=False)
        return table
