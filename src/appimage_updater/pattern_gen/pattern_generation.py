"""Pattern generation utilities for the pattern generator.

This module contains functions for creating regex patterns from filenames,
including prefix extraction, generalization, and fallback pattern creation.
"""

import re
import urllib.parse

from loguru import logger


def create_pattern_from_filenames(filenames: list[str], include_both_formats: bool = False) -> str:
    """Create a regex pattern from actual AppImage/ZIP filenames."""
    if not filenames:
        return _build_pattern("", include_both_formats, empty_ok=True)

    base_filenames = _strip_extensions_list(filenames)
    prefix = _derive_common_prefix(base_filenames, filenames)
    prefix = _generalize_pattern_prefix(prefix)

    pattern = _build_pattern(prefix, include_both_formats)
    logger.debug(f"Generated pattern from {len(filenames)} files: {pattern}")
    return pattern


def _strip_extensions_list(filenames: list[str]) -> list[str]:
    exts = (".AppImage", ".appimage", ".zip", ".ZIP")
    result = []
    for name in filenames:
        for ext in exts:
            if name.endswith(ext):
                result.append(name[: -len(ext)])
                break
        else:
            result.append(name)
    return result


def _derive_common_prefix(base_filenames: list[str], original: list[str]) -> str:
    common = find_common_prefix(base_filenames)
    if len(common) >= 2:
        return common
    first_file = original[0] if original else ""
    match = re.match(r"^([^-_]+)", first_file)
    return match.group(1) if match else first_file.split("-")[0]


def _build_pattern(prefix: str, include_both_formats: bool, empty_ok: bool = False) -> str:
    if not prefix and empty_ok:
        ext = "\\.(zip|AppImage)" if include_both_formats else "\\.AppImage"
        return f".*{ext}(\\.(|current|old))?$"
    escaped = re.escape(prefix)
    ext = "\\.(zip|AppImage)" if include_both_formats else "\\.AppImage"
    return f"(?i){escaped}.*{ext}(\\.(|current|old))?$"


def _remove_version_and_date_patterns(prefix: str) -> str:
    """Remove version numbers and date patterns from prefix."""
    # Handle standard versions: "_1.0.2" or "_v1.0.2" or "-1.0.2"
    prefix = re.sub(r"[_-]v?\d+(\.\d+)*", "", prefix)
    # Handle date patterns: "_2024-01-15" or "-20240115"
    prefix = re.sub(r"[_-]\d{4}[-_]?\d{2}[-_]?\d{2}", "", prefix)
    # Handle build numbers: "_build123" or "-b456"
    prefix = re.sub(r"[_-](build|b)\d+", "", prefix, flags=re.IGNORECASE)
    # Handle commit hashes: "_abc123def" (7+ hex chars)
    prefix = re.sub(r"[_-][a-f0-9]{7,}", "", prefix, flags=re.IGNORECASE)

    return prefix


def _get_platform_patterns() -> list[str]:
    """Get list of platform patterns to remove from middle of prefix."""
    return [
        r"[_-]conda[_-]Linux[_-]",  # -conda-Linux- or _conda_Linux_
        r"[_-]linux[_-]x86_64[_-]",  # -linux-x86_64- or _linux_x86_64_
        r"[_-]x86_64[_-]linux[_-]",  # -x86_64-linux- or _x86_64_linux_
        r"[_-]ubuntu[_-]\d+\.\d+[_-]",  # -ubuntu-20.04- or _ubuntu_22.04_
        r"[_-]x86_64[_-]",  # -x86_64- or _x86_64_
    ]


def _get_suffix_patterns() -> list[str]:
    """Get list of suffix patterns to remove from end of prefix."""
    return [
        r"[_-]conda$",
        r"[_-]linux$",
        r"[_-]x86_64$",
        r"[_-]amd64$",
        r"[_-]ubuntu$",
        r"[_-]fedora$",
        r"[_-]debian$",
        r"[_-]appimage$",
        r"[_-]portable$",
    ]


def _remove_platform_patterns(prefix: str) -> str:
    """Remove platform patterns from prefix."""
    # Remove platform patterns that appear in the middle
    for pattern in _get_platform_patterns():
        prefix = re.sub(pattern, "-", prefix, flags=re.IGNORECASE)

    # Remove platform patterns that appear at the end
    for pattern in _get_suffix_patterns():
        prefix = re.sub(pattern, "", prefix, flags=re.IGNORECASE)

    return prefix


def _ensure_meaningful_prefix(prefix: str) -> str:
    """Ensure prefix has meaningful content, extract app name if over-generalized."""
    if len(prefix) < 2:
        # If we've over-generalized, try to extract just the app name
        # This is a fallback - in practice we should have better data
        logger.debug("Prefix too short after generalization, using minimal pattern")
        return ""

    return prefix


def _generalize_pattern_prefix(prefix: str) -> str:
    """Generalize a pattern prefix by removing version numbers and overly specific details.

    This helps create patterns that work across multiple releases rather than being
    tied to specific versions or build details.
    """
    # Remove version numbers and dates
    prefix = _remove_version_and_date_patterns(prefix)

    # Remove platform-specific patterns
    prefix = _remove_platform_patterns(prefix)

    # Clean up any double separators or trailing separators
    prefix = re.sub(r"[_-]+", "-", prefix)  # Multiple separators -> single dash
    prefix = prefix.strip("-_")  # Remove leading/trailing separators

    # Ensure we still have meaningful content
    prefix = _ensure_meaningful_prefix(prefix)

    return prefix


def _find_common_length(str1: str, str2: str) -> int:
    """Find the length of common prefix between two strings."""
    common_len = 0
    min_len = min(len(str1), len(str2))

    for i in range(min_len):
        if str1[i].lower() == str2[i].lower():
            common_len += 1
        else:
            break

    return common_len


def find_common_prefix(strings: list[str]) -> str:
    """Find the longest common prefix among a list of strings."""
    if not strings:
        return ""

    if len(strings) == 1:
        return strings[0]

    # Start with the first string as the initial prefix
    prefix = strings[0]

    # Compare with each subsequent string
    for string in strings[1:]:
        common_len = _find_common_length(prefix, string)
        prefix = prefix[:common_len]

        # If no common prefix, break early
        if not prefix:
            break

    return prefix


def generate_fallback_pattern(app_name: str, url: str) -> str:
    """Generate a fallback pattern using app name and URL heuristics.

    This is the original logic, kept as a fallback when we can't fetch
    releases or when no suitable files are found.
    """
    # Extract potential app name from URL if not provided
    if not app_name and url:
        try:
            parsed = urllib.parse.urlparse(url)
            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) >= 2:
                app_name = path_parts[1]  # Use repo name
        except Exception as e:
            logger.debug(f"Failed to extract app name from URL: {e}")

    if not app_name:
        # Ultimate fallback - match any AppImage
        pattern = r".*\.AppImage(\.(|current|old))?$"
        logger.debug("No app name available, using universal pattern")
        return pattern

    # Clean up app name for pattern use
    clean_name = re.sub(r"[^a-zA-Z0-9]", "", app_name.lower())
    if len(clean_name) < 2:
        clean_name = app_name.lower()

    # Create case-insensitive pattern
    pattern = f"(?i){re.escape(clean_name)}.*\\.AppImage(\\.(|current|old))?$"
    logger.debug(f"Generated fallback pattern for '{app_name}': {pattern}")

    return pattern
