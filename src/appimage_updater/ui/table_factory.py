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

    @staticmethod
    def create_check_results_table(title: str = "Update Check Results", dry_run: bool = False) -> Table:
        """Create table for check command results.

        Args:
            title: Table title
            dry_run: Whether this is a dry-run check

        Returns:
            Configured Rich Table instance
        """
        table = Table(title=title)
        table.add_column("Application", style="cyan", no_wrap=True)
        table.add_column("Status", style="bold", no_wrap=True)
        table.add_column("Current", style="yellow", no_wrap=True)
        table.add_column("Latest", style="green", no_wrap=True)

        if not dry_run:
            table.add_column("URL", style="blue", no_wrap=False, overflow="fold")

        return table
