"""Init command implementation."""

from __future__ import annotations

from loguru import logger
from rich.console import Console

from ..logging_config import configure_logging
from .base import Command, CommandResult
from .parameters import InitParams


class InitCommand(Command):
    """Command to initialize configuration."""

    def __init__(self, params: InitParams):
        self.params = params
        self.console = Console()

    def validate(self) -> list[str]:
        """Validate command parameters."""
        # Init command has no required parameters
        return []

    async def execute(self) -> CommandResult:
        """Execute the init command."""
        configure_logging(debug=self.params.debug)

        try:
            # Execute the init operation
            await self._execute_init_operation()

            return CommandResult(success=True, message="Initialization completed successfully")

        except Exception as e:
            logger.error(f"Unexpected error in init command: {e}")
            logger.exception("Full exception details")
            return CommandResult(success=False, message=str(e), exit_code=1)

    async def _execute_init_operation(self) -> None:
        """Execute the core init operation logic."""
        try:
            # Import required modules and implement init logic
            import json
            from pathlib import Path

            from ..config_loader import get_default_config_path

            # Determine target location
            if self.params.config_dir:
                target_dir = Path(self.params.config_dir)

                # Check if directory already exists
                if target_dir.exists():
                    self.console.print(f"Configuration directory already exists at: {target_dir}")
                    return

                target_dir.mkdir(parents=True, exist_ok=True)
                config_file = target_dir / "freecad.json"
            else:
                config_file = get_default_config_path()
                config_file.parent.mkdir(parents=True, exist_ok=True)

            # Create example FreeCAD configuration
            example_config = {
                "applications": [
                    {
                        "name": "FreeCAD",
                        "source_type": "github",
                        "url": "https://github.com/FreeCAD/FreeCAD",
                        "download_dir": str(Path.home() / "Applications"),
                        "pattern": "FreeCAD.*\\.AppImage$",
                        "enabled": True,
                        "prerelease": False,
                        "checksum": {
                            "enabled": False,
                            "pattern": "{filename}.sha256",
                            "algorithm": "sha256",
                            "required": False,
                        },
                        "rotation_enabled": False,
                        "symlink_path": None,
                        "retain_count": 3,
                    }
                ]
            }

            # Write the example configuration
            with config_file.open("w") as f:
                json.dump(example_config, f, indent=2)

            self.console.print(f"Configuration initialized at: {config_file}")
        except Exception as e:
            logger.error(f"Unexpected error in init command: {e}")
            logger.exception("Full exception details")
            raise
