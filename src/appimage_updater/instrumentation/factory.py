"""Factory functions for creating HTTP instrumentation components."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..commands.parameters import CheckParams, RepositoryParams

from .http_tracker import HTTPTracker
from .logging_interface import create_default_http_logger, create_trace_http_logger


def create_http_tracker_from_params(params: CheckParams | RepositoryParams) -> HTTPTracker | None:
    """Create HTTP tracker based on command parameters.

    Args:
        params: Command parameters containing HTTP instrumentation settings

    Returns:
        HTTPTracker instance if instrumentation is enabled, None otherwise
    """
    # Check if any HTTP tracking is enabled
    if not (params.instrument_http or params.trace):
        return None

    # If trace is enabled, use trace logger regardless of other settings
    if params.trace:
        trace_logger = create_trace_http_logger(use_rich=True)
        return HTTPTracker(
            stack_depth=params.http_stack_depth, track_headers=params.http_track_headers, logger=trace_logger
        )
    else:
        # Use regular instrumentation logger
        verbose = params.debug if hasattr(params, "debug") else False
        logger = create_default_http_logger(verbose=verbose)
        return HTTPTracker(stack_depth=params.http_stack_depth, track_headers=params.http_track_headers, logger=logger)
