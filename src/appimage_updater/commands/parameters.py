"""Parameter objects for command pattern implementation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class BaseParams:
    """Base parameters common to most commands."""

    config_file: Path | None = None
    config_dir: Path | None = None
    debug: bool = False
    verbose: bool = False


@dataclass
class AddParams(BaseParams):
    """Parameters for add command."""

    name: str | None = None
    url: str | None = None
    download_dir: str | None = None
    create_dir: bool = False
    yes: bool = False
    rotation: bool | None = None
    retain: int = 5
    symlink: str | None = None
    prerelease: bool | None = None
    checksum: bool | None = None
    checksum_algorithm: str = "sha256"
    checksum_pattern: str = ""
    checksum_required: bool | None = None
    pattern: str | None = None
    direct: bool | None = None
    auto_subdir: bool | None = None
    dry_run: bool = False
    interactive: bool = False
    examples: bool = False
    format: Any = None  # OutputFormat, avoiding circular import


@dataclass
class CheckParams(BaseParams):
    """Parameters for check command."""

    app_names: list[str] | None = None
    dry_run: bool = False
    yes: bool = False
    no_interactive: bool = False
    info: bool = False
    # HTTP instrumentation options
    instrument_http: bool = False
    http_stack_depth: int = 4
    http_track_headers: bool = False
    # Output formatting options
    format: str = "rich"


@dataclass
class EditParams(BaseParams):
    """Parameters for edit command."""

    app_names: list[str] | None = None
    url: str | None = None
    download_dir: str | None = None
    pattern: str | None = None
    rotation: bool | None = None
    retain_count: int | None = None
    symlink_path: str | None = None
    prerelease: bool | None = None
    checksum: bool | None = None
    checksum_algorithm: str | None = None
    checksum_pattern: str | None = None
    checksum_required: bool | None = None
    direct: bool | None = None
    enable: bool | None = None
    force: bool = False
    create_dir: bool = False
    yes: bool = False
    auto_subdir: bool | None = None
    dry_run: bool = False
    format: Any = None  # OutputFormat, avoiding circular import


@dataclass
class ShowParams(BaseParams):
    """Parameters for show command."""

    app_names: list[str] | None = None
    format: Any = None  # OutputFormat, avoiding circular import


@dataclass
class ListParams:
    """Parameters for list command."""

    config_file: Path | None = None
    config_dir: Path | None = None
    debug: bool = False
    format: Any = None  # OutputFormat, avoiding circular import


@dataclass
class RemoveParams(BaseParams):
    """Parameters for remove command."""

    app_names: list[str] | None = None
    force: bool = False
    format: Any = None  # OutputFormat, avoiding circular import
    yes: bool = False


@dataclass
class RepositoryParams(BaseParams):
    """Parameters for repository command."""

    app_names: list[str] | None = None
    assets: bool = False
    limit: int = 10
    dry_run: bool = False
    instrument_http: bool = False
    http_stack_depth: int = 3
    http_track_headers: bool = False
    format: Any = None  # OutputFormat, avoiding circular import


# InitParams removed with init command


@dataclass
class ConfigParams(BaseParams):
    """Parameters for config command."""

    action: str = ""
    setting: str = ""
    value: str = ""
    app_name: str = ""
    format: Any = None  # OutputFormat, avoiding circular import
