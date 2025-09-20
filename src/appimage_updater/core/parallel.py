"""Parallel processing utilities for AppImage Updater."""

from __future__ import annotations

import asyncio
import multiprocessing
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from typing import Any

from loguru import logger


def check_app_worker(app_config_dict: dict[str, Any]) -> dict[str, Any]:
    """Worker function for checking a single application in a separate process.

    This function is designed to be run in a separate process, so it needs to:
    1. Import all necessary modules within the function
    2. Reconstruct objects from serializable data
    3. Return serializable results

    Args:
        app_config_dict: Serialized application configuration

    Returns:
        Serialized check result
    """
    try:
        # Import modules within the worker to avoid pickling issues
        from ..config.models import ApplicationConfig
        from ..core.version_checker import VersionChecker

        # Reconstruct the application config from the dictionary
        app_config = ApplicationConfig(**app_config_dict)

        # Create version checker (non-interactive in worker processes)
        version_checker = VersionChecker(interactive=False)

        # Run the check synchronously in this process
        # We need to create a new event loop for this process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(version_checker.check_for_updates(app_config))

            # Convert result to serializable format
            return {
                "success": result.success,
                "app_name": app_config.name,
                "candidate": _serialize_candidate(result.candidate) if result.candidate else None,
                "error_message": result.error_message,
            }
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Error in worker process for app {app_config_dict.get('name', 'unknown')}: {e}")
        return {
            "success": False,
            "app_name": app_config_dict.get("name", "unknown"),
            "candidate": None,
            "error_message": str(e),
        }


def _serialize_candidate(candidate: Any) -> dict[str, Any] | None:
    """Serialize an UpdateCandidate for inter-process communication."""
    if not candidate:
        return None

    try:
        # Use model_dump if available (Pydantic v2), otherwise use dict()
        if hasattr(candidate, "model_dump"):
            return candidate.model_dump()  # type: ignore[no-any-return]
        elif hasattr(candidate, "dict"):
            return candidate.dict()  # type: ignore[no-any-return]
        else:
            # Fallback to manual serialization
            return {
                "app_name": candidate.app_name,
                "current_version": candidate.current_version,
                "latest_version": candidate.latest_version,
                "download_path": str(candidate.download_path) if candidate.download_path else None,
                "is_newer": candidate.is_newer,
                "checksum_required": getattr(candidate, "checksum_required", False),
            }
    except Exception as e:
        logger.error(f"Error serializing candidate: {e}")
        return None


def _deserialize_candidate(candidate_dict: dict[str, Any] | None) -> Any:
    """Deserialize an UpdateCandidate from inter-process communication."""
    if not candidate_dict:
        return None

    try:
        from datetime import datetime
        from pathlib import Path

        from ..core.models import Asset, UpdateCandidate

        # Handle asset deserialization if present
        asset_data = candidate_dict.get("asset")
        asset = Asset(**asset_data) if asset_data else Asset(name="unknown", url="", size=0, created_at=datetime.now())

        # Create UpdateCandidate with required fields
        return UpdateCandidate(
            app_name=candidate_dict["app_name"],
            current_version=candidate_dict.get("current_version"),
            latest_version=candidate_dict["latest_version"],
            asset=asset,
            download_path=Path(candidate_dict["download_path"]) if candidate_dict.get("download_path") else Path(),
            is_newer=candidate_dict.get("is_newer", True),
            checksum_required=candidate_dict.get("checksum_required", False),
        )
    except Exception as e:
        logger.error(f"Error deserializing candidate: {e}")
        return None


class ParallelProcessor:
    """Handles parallel processing of application checks."""

    def __init__(self, enable_multiple_processes: bool = True, process_pool_size: int = 4):
        """Initialize the parallel processor.

        Args:
            enable_multiple_processes: Whether to use multiple processes
            process_pool_size: Number of processes in the pool
        """
        self.enable_multiple_processes = enable_multiple_processes
        self.process_pool_size = min(process_pool_size, multiprocessing.cpu_count())

    async def process_applications(
        self, applications: list[Any], worker_func: Callable[[dict[str, Any]], dict[str, Any]]
    ) -> list[Any]:
        """Process applications either in parallel or sequentially.

        Args:
            applications: List of application configurations
            worker_func: Worker function to process each application

        Returns:
            List of processing results
        """
        if not self.enable_multiple_processes or len(applications) <= 1:
            return await self._process_sequential(applications, worker_func)
        else:
            return await self._process_parallel(applications, worker_func)

    async def _process_sequential(
        self, applications: list[Any], worker_func: Callable[[dict[str, Any]], dict[str, Any]]
    ) -> list[Any]:
        """Process applications sequentially using asyncio."""
        logger.debug("Processing applications sequentially with asyncio")

        # Use the existing asyncio-based approach for sequential processing
        from ..core.version_checker import VersionChecker

        version_checker = VersionChecker(interactive=False)
        check_tasks = [version_checker.check_for_updates(app) for app in applications]

        return await asyncio.gather(*check_tasks)

    async def _process_parallel(
        self, applications: list[Any], worker_func: Callable[[dict[str, Any]], dict[str, Any]]
    ) -> list[Any]:
        """Process applications in parallel using ProcessPoolExecutor."""
        logger.debug(f"Processing {len(applications)} applications in parallel with {self.process_pool_size} processes")

        # Serialize application configs for inter-process communication
        app_dicts = []
        for app in applications:
            try:
                app_dict = app.model_dump() if hasattr(app, "model_dump") else app.__dict__
                app_dicts.append(app_dict)
            except Exception as e:
                logger.error(f"Error serializing app config for {getattr(app, 'name', 'unknown')}: {e}")
                # Create a fallback result for this app
                app_dicts.append({"name": getattr(app, "name", "unknown"), "error": str(e)})

        # Process in parallel using ProcessPoolExecutor
        loop = asyncio.get_event_loop()

        with ProcessPoolExecutor(max_workers=self.process_pool_size) as executor:
            # Submit all tasks to the process pool
            futures = [loop.run_in_executor(executor, worker_func, app_dict) for app_dict in app_dicts]

            # Wait for all tasks to complete
            results = await asyncio.gather(*futures, return_exceptions=True)

        # Convert results back to the expected format
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Process pool task failed for app {i}: {result}")
                # Create a failure result
                from ..core.models import CheckResult

                processed_results.append(
                    CheckResult(
                        success=False,
                        app_name=applications[i].name if i < len(applications) else "unknown",
                        candidate=None,
                        error_message=str(result),
                    )
                )
            else:
                # Convert the serialized result back to a CheckResult
                if isinstance(result, dict):
                    processed_results.append(self._deserialize_check_result(result))
                else:
                    # Handle unexpected result type
                    from ..core.models import CheckResult

                    processed_results.append(
                        CheckResult(
                            success=False,
                            app_name="unknown",
                            candidate=None,
                            error_message=f"Unexpected result type: {type(result)}",
                        )
                    )

        return processed_results

    def _deserialize_check_result(self, result_dict: dict[str, Any]) -> Any:
        """Convert a serialized result back to a CheckResult object."""
        try:
            from ..core.models import CheckResult

            candidate = _deserialize_candidate(result_dict.get("candidate"))

            return CheckResult(
                success=result_dict["success"],
                app_name=result_dict["app_name"],
                candidate=candidate,
                error_message=result_dict.get("error_message"),
            )
        except Exception as e:
            logger.error(f"Error deserializing check result: {e}")
            from ..core.models import CheckResult

            return CheckResult(
                success=False,
                app_name=result_dict.get("app_name", "unknown"),
                candidate=None,
                error_message=f"Deserialization error: {e}",
            )


def get_effective_parallelization_settings(
    config: Any,
    enable_multiple_processes_override: bool | None = None,
    process_pool_size_override: int | None = None,
) -> tuple[bool, int]:
    """Get effective parallelization settings from config and overrides.

    Args:
        config: Configuration object
        enable_multiple_processes_override: CLI override for enable_multiple_processes
        process_pool_size_override: CLI override for process_pool_size

    Returns:
        Tuple of (enable_multiple_processes, process_pool_size)
    """
    # Get defaults from config
    defaults = config.global_config.defaults
    enable_multiple_processes = defaults.enable_multiple_processes
    process_pool_size = defaults.process_pool_size

    # Apply CLI overrides if provided
    if enable_multiple_processes_override is not None:
        enable_multiple_processes = enable_multiple_processes_override

    if process_pool_size_override is not None:
        process_pool_size = process_pool_size_override

    # Ensure process_pool_size is within valid range
    process_pool_size = max(1, min(process_pool_size, 16))

    logger.debug(
        f"Effective parallelization settings: enable_multiple_processes={enable_multiple_processes}, "
        f"process_pool_size={process_pool_size}"
    )

    return enable_multiple_processes, process_pool_size
