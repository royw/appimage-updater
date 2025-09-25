"""Main application entry point using CLI encapsulation architecture.

This module provides the main CLI entry point and maintains backward compatibility
for tests that import the 'app' object.
"""

from __future__ import annotations

from .cli.application import AppImageUpdaterCLI


# Create CLI application instance
_cli_app = AppImageUpdaterCLI()

# Backward compatibility: export the typer app for tests
app = _cli_app.app


def cli_main() -> None:
    """Main CLI entry point using the new CLI architecture."""
    _cli_app.run()


if __name__ == "__main__":
    cli_main()
