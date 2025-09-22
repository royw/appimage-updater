"""Deprecation utilities for configuration functions."""

import functools
import warnings
from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def deprecated(reason: str, replacement: str | None = None) -> Callable[[F], F]:
    """Mark a function as deprecated.

    Args:
        reason: Reason for deprecation
        replacement: Suggested replacement (optional)

    Returns:
        Decorated function that issues deprecation warnings
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            message = f"{func.__name__} is deprecated: {reason}"
            if replacement:
                message += f" Use {replacement} instead."

            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator
