"""New main application entry point using CLI encapsulation.

This is the new main entry point that uses the encapsulated CLI architecture.
Once migration is complete, this will replace main.py.
"""

from __future__ import annotations

from .cli.application import AppImageUpdaterCLI


def cli_main() -> None:
    """Main CLI entry point using the new CLI architecture."""
    cli_app = AppImageUpdaterCLI()
    cli_app.run()


if __name__ == "__main__":
    cli_main()
