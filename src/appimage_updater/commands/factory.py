"""Command factory for creating command instances."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .add_command import AddCommand
from .check_command import CheckCommand
from .config_command import ConfigCommand
from .edit_command import EditCommand

# InitCommand removed
from .list_command import ListCommand
from .parameters import (
    AddParams,
    CheckParams,
    ConfigParams,
    EditParams,
    ListParams,
    RemoveParams,
    RepositoryParams,
    ShowParams,
)
from .remove_command import RemoveCommand
from .repository_command import RepositoryCommand
from .show_command import ShowCommand


class CommandFactory:
    """Factory for creating command instances from CLI parameters."""

    @staticmethod
    def create_add_command(
        name: str | None = None,
        url: str | None = None,
        download_dir: str | None = None,
        create_dir: bool = False,
        yes: bool = False,
        config_file: Path | None = None,
        config_dir: Path | None = None,
        rotation: bool | None = None,
        retain: int = 5,
        symlink: str | None = None,
        prerelease: bool | None = None,
        basename: str | None = None,
        checksum: bool | None = None,
        checksum_algorithm: str = "sha256",
        checksum_pattern: str = "",
        checksum_required: bool | None = None,
        pattern: str | None = None,
        direct: bool | None = None,
        auto_subdir: bool | None = None,
        verbose: bool = False,
        dry_run: bool = False,
        interactive: bool = False,
        examples: bool = False,
        debug: bool = False,
        format: Any = None,
    ) -> AddCommand:
        """Create an AddCommand instance."""
        params = AddParams(
            name=name,
            url=url,
            download_dir=download_dir,
            create_dir=create_dir,
            yes=yes,
            config_file=config_file,
            config_dir=config_dir,
            rotation=rotation,
            retain=retain,
            symlink=symlink,
            prerelease=prerelease,
            basename=basename,
            checksum=checksum,
            checksum_algorithm=checksum_algorithm,
            checksum_pattern=checksum_pattern,
            checksum_required=checksum_required,
            pattern=pattern,
            direct=direct,
            auto_subdir=auto_subdir,
            verbose=verbose,
            dry_run=dry_run,
            interactive=interactive,
            examples=examples,
            debug=debug,
            format=format,
        )
        return AddCommand(params)

    @staticmethod
    def create_check_command(
        app_names: list[str] | None = None,
        config_file: Path | None = None,
        config_dir: Path | None = None,
        dry_run: bool = False,
        yes: bool = False,
        no_interactive: bool = False,
        verbose: bool = False,
        debug: bool = False,
        info: bool = False,
        instrument_http: bool = False,
        http_stack_depth: int = 4,
        http_track_headers: bool = False,
        format: str = "rich",
    ) -> CheckCommand:
        """Create a CheckCommand instance."""
        params = CheckParams(
            app_names=app_names,
            config_file=config_file,
            config_dir=config_dir,
            dry_run=dry_run,
            yes=yes,
            no_interactive=no_interactive,
            verbose=verbose,
            debug=debug,
            info=info,
            instrument_http=instrument_http,
            http_stack_depth=http_stack_depth,
            http_track_headers=http_track_headers,
            format=format,
        )
        return CheckCommand(params)

    @staticmethod
    def create_edit_command(
        app_names: list[str] | None = None,
        config_file: Path | None = None,
        config_dir: Path | None = None,
        url: str | None = None,
        download_dir: str | None = None,
        basename: str | None = None,
        pattern: str | None = None,
        rotation: bool | None = None,
        retain_count: int | None = None,
        symlink_path: str | None = None,
        prerelease: bool | None = None,
        checksum: bool | None = None,
        checksum_algorithm: str | None = None,
        checksum_pattern: str | None = None,
        checksum_required: bool | None = None,
        direct: bool | None = None,
        enable: bool | None = None,
        force: bool = False,
        create_dir: bool = False,
        yes: bool = False,
        auto_subdir: bool | None = None,
        verbose: bool = False,
        dry_run: bool = False,
        debug: bool = False,
        format: Any = None,
    ) -> EditCommand:
        """Create an EditCommand instance."""
        params = EditParams(
            app_names=app_names,
            config_file=config_file,
            config_dir=config_dir,
            url=url,
            download_dir=download_dir,
            basename=basename,
            pattern=pattern,
            rotation=rotation,
            retain_count=retain_count,
            symlink_path=symlink_path,
            prerelease=prerelease,
            checksum=checksum,
            checksum_algorithm=checksum_algorithm,
            checksum_pattern=checksum_pattern,
            checksum_required=checksum_required,
            direct=direct,
            enable=enable,
            force=force,
            create_dir=create_dir,
            yes=yes,
            auto_subdir=auto_subdir,
            verbose=verbose,
            dry_run=dry_run,
            debug=debug,
            format=format,
        )
        return EditCommand(params)

    @staticmethod
    def create_show_command(
        app_names: list[str] | None = None,
        config_file: Path | None = None,
        config_dir: Path | None = None,
        verbose: bool = False,
        debug: bool = False,
        format: Any = None,
    ) -> ShowCommand:
        """Create a ShowCommand instance."""
        params = ShowParams(
            app_names=app_names,
            config_file=config_file,
            config_dir=config_dir,
            verbose=verbose,
            debug=debug,
            format=format,
        )
        return ShowCommand(params)

    @staticmethod
    def create_list_command(
        config_file: Path | None = None,
        config_dir: Path | None = None,
        debug: bool = False,
        format: Any = None,
    ) -> ListCommand:
        """Create a ListCommand instance."""
        params = ListParams(
            config_file=config_file,
            config_dir=config_dir,
            debug=debug,
            format=format,
        )
        return ListCommand(params)

    @staticmethod
    def create_remove_command(
        app_names: list[str] | None = None,
        config_file: Path | None = None,
        config_dir: Path | None = None,
        yes: bool = False,
        verbose: bool = False,
        debug: bool = False,
        format: Any = None,
    ) -> RemoveCommand:
        """Create a RemoveCommand instance."""
        params = RemoveParams(
            app_names=app_names,
            config_file=config_file,
            config_dir=config_dir,
            yes=yes,
            verbose=verbose,
            debug=debug,
            format=format,
        )
        return RemoveCommand(params)

    @staticmethod
    def create_repository_command(
        app_names: list[str] | None = None,
        config_file: Path | None = None,
        config_dir: Path | None = None,
        assets: bool = False,
        limit: int = 10,
        dry_run: bool = False,
        instrument_http: bool = False,
        http_stack_depth: int = 3,
        http_track_headers: bool = False,
        verbose: bool = False,
        debug: bool = False,
        format: Any = None,
    ) -> RepositoryCommand:
        """Create a RepositoryCommand instance."""
        params = RepositoryParams(
            app_names=app_names,
            config_file=config_file,
            config_dir=config_dir,
            assets=assets,
            limit=limit,
            dry_run=dry_run,
            instrument_http=instrument_http,
            http_stack_depth=http_stack_depth,
            http_track_headers=http_track_headers,
            verbose=verbose,
            debug=debug,
            format=format,
        )
        return RepositoryCommand(params)

    # create_init_command removed with InitCommand

    @staticmethod
    def create_config_command(
        action: str,
        setting: str = "",
        value: str = "",
        app_name: str = "",
        config_file: Path | None = None,
        config_dir: Path | None = None,
        debug: bool = False,
        format: Any = None,
    ) -> ConfigCommand:
        """Create a ConfigCommand instance."""
        params = ConfigParams(
            action=action,
            setting=setting,
            value=value,
            app_name=app_name,
            config_file=config_file,
            config_dir=config_dir,
            debug=debug,
            format=format,
        )
        return ConfigCommand(params)
