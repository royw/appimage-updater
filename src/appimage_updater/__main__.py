"""Entry point for running appimage_updater as a module."""

import os


# Disable rich traceback before any imports
os.environ["_RICH_TRACEBACK"] = "0"
os.environ["PYTHONPATH"] = os.environ.get("PYTHONPATH", "")

from .main import cli_main


if __name__ == "__main__":
    cli_main()
