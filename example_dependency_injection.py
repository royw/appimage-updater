#!/usr/bin/env python3
"""Example of how dependency injection would work for HTTP tracking."""

from appimage_updater.commands.check_command import CheckCommand
from appimage_updater.commands.parameters import CheckParams
from appimage_updater.instrumentation.http_tracker import HTTPTracker
from appimage_updater.instrumentation.logging_interface import (
    create_default_http_logger,
    create_silent_http_logger
)


async def example_usage():
    """Example of how the dependency injection approach would work."""
    
    # Create command parameters
    params = CheckParams(
        debug=False,
        dry_run=True,
        instrument_http=True,  # This flag is now just for CLI parsing
        http_stack_depth=4,
        http_track_headers=False
    )
    
    # Create the command
    command = CheckCommand(params)
    
    # === APPROACH 1: No HTTP tracking ===
    print("=== Running without HTTP tracking ===")
    result = await command.execute()  # No tracker = no instrumentation
    
    
    # === APPROACH 2: Default HTTP tracking ===
    print("\n=== Running with default HTTP tracking ===")
    tracker = HTTPTracker()  # Uses default debug-level logging
    result = await command.execute(http_tracker=tracker)
    
    
    # === APPROACH 3: Custom HTTP tracking ===
    print("\n=== Running with custom HTTP tracking ===")
    custom_logger = create_default_http_logger(verbose=False)  # Your preference
    custom_tracker = HTTPTracker(
        stack_depth=params.http_stack_depth,
        track_headers=params.http_track_headers,
        logger=custom_logger
    )
    result = await command.execute(http_tracker=custom_tracker)
    
    
    # === APPROACH 4: Silent HTTP tracking (for testing) ===
    print("\n=== Running with silent HTTP tracking (testing) ===")
    silent_logger = create_silent_http_logger()
    test_tracker = HTTPTracker(logger=silent_logger)
    result = await command.execute(http_tracker=test_tracker)
    
    # You can still analyze the requests even with silent logging
    print(f"Captured {len(test_tracker.requests)} HTTP requests silently")


def create_tracker_from_params(params: CheckParams) -> HTTPTracker | None:
    """Factory function to create HTTP tracker based on parameters."""
    if not params.instrument_http:
        return None
    
    # Create logger based on debug level or other preferences
    if params.debug:
        logger = create_default_http_logger(verbose=True)  # More verbose
    else:
        logger = create_default_http_logger(verbose=False)  # Quiet
    
    return HTTPTracker(
        stack_depth=params.http_stack_depth,
        track_headers=params.http_track_headers,
        logger=logger
    )


async def cli_style_usage():
    """Example of how this would work in your CLI."""
    
    # Parse CLI arguments into params
    params = CheckParams(
        debug=False,
        instrument_http=True,
        http_stack_depth=4,
        http_track_headers=False
    )
    
    # Create command
    command = CheckCommand(params)
    
    # Create tracker based on params (or None if not requested)
    tracker = create_tracker_from_params(params)
    
    # Execute with optional tracker
    result = await command.execute(http_tracker=tracker)
    
    return result


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
