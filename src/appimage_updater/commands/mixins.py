"""Mixins for command functionality."""


class FormatterContextMixin:
    """Mixin for handling output formatter context.

    This mixin is used to mark commands that support output formatting.
    Commands that inherit from this mixin can use OutputFormatterContext
    to make formatters available throughout their execution.
    """

    pass
