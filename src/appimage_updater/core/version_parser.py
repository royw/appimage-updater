"""Unified version parsing for filenames, URLs, and version strings.

This module provides centralized version extraction and normalization functionality
that can be used across the entire application for consistent version handling.
"""

from __future__ import annotations

from collections.abc import Callable
import re

from appimage_updater.utils.version_utils import normalize_version_string


class VersionParser:
    """Unified version parsing for filenames, URLs, and version strings."""

    def clean_filename_for_version_extraction(self, filename: str) -> str:
        """Clean filename by removing git hashes and other variable identifiers.

        This prevents interference with version extraction.
        """
        # Remove file extension
        cleaned = re.sub(r"\.AppImage$", "", filename, flags=re.IGNORECASE)

        # Remove git commit hashes (6-8 hex characters, typically 7)
        # This prevents extracting parts of git hashes as version numbers
        cleaned = re.sub(r"-[a-fA-F0-9]{6,8}(?=-|$)", "", cleaned)

        # Remove architecture identifiers that might contain numbers
        cleaned = re.sub(r"-(x86_64|amd64|i386|i686|arm64|armv7|armhf)(?=-|$)", "", cleaned)

        # Remove platform identifiers
        cleaned = re.sub(r"-(linux|win32|win64|windows|macos|darwin)(?=-|$)", "", cleaned, flags=re.IGNORECASE)

        # Clean up any double hyphens or trailing hyphens
        cleaned = re.sub(r"-+", "-", cleaned)
        cleaned = cleaned.strip("-")

        return cleaned

    def extract_version_from_filename(self, filename: str) -> str | None:
        """Extract version from filename using common patterns."""
        # First, eliminate git commit hashes and other variable identifiers to avoid false matches
        cleaned_filename = self.clean_filename_for_version_extraction(filename)

        # Test each pattern in order of specificity
        patterns: list[Callable[[str], str | None]] = [
            self._extract_prerelease_version,
            self._extract_date_version,
            self._extract_semantic_version,
            self._extract_two_part_version,
            self._extract_single_number_version,
        ]

        for pattern_func in patterns:
            result = pattern_func(cleaned_filename)
            if result:
                # Normalize the extracted version
                return normalize_version_string(result)

        # Return None if no version pattern found
        return None

    def normalize_version_string(self, version: str) -> str:
        """Normalize version strings consistently."""
        return normalize_version_string(version)

    def generate_flexible_pattern_from_filename(self, filename: str) -> str:
        """Generate a flexible regex pattern from a filename by eliminating variable identifiers."""
        # Start with the filename
        pattern = filename

        # Remove file extension to work with base name
        base_name = re.sub(r"\.AppImage$", "", pattern, flags=re.IGNORECASE)

        # Eliminate git commit hashes (6-8 hex characters, typically 7)
        base_name = re.sub(r"-[a-fA-F0-9]{6,8}(?=-|$)", "", base_name)

        # Eliminate architecture identifiers
        base_name = re.sub(r"-(x86_64|amd64|i386|i686|arm64|armv7|armhf)(?=-|$)", "", base_name)

        # Eliminate platform identifiers
        base_name = re.sub(r"-(linux|win32|win64|windows|macos|darwin)(?=-|$)", "", base_name, flags=re.IGNORECASE)

        # Eliminate version numbers (semantic versions)
        base_name = re.sub(r"-\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9]+)?(?=-|$)", "", base_name)

        # Clean up any double hyphens or trailing hyphens
        base_name = re.sub(r"-+", "-", base_name)
        base_name = base_name.strip("-")

        # Create flexible pattern that matches the cleaned base name with any suffixes
        escaped_base = re.escape(base_name)
        return f"(?i)^{escaped_base}.*\\.AppImage$"

    def _extract_prerelease_version(self, filename: str) -> str | None:
        """Extract pre-release versions like '2.3.1-alpha'."""
        # Only match if followed by word boundary to avoid false matches like '1.0.2-conda'
        pattern = r"[vV]?(\d+\.\d+\.\d+(?:\.\d+)?-(?:alpha|beta|rc|dev|pre))(?=\W|$)"
        match = re.search(pattern, filename, re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_date_version(self, filename: str) -> str | None:
        """Extract date formats like '2025.09.03'."""
        pattern = r"(\d{4}[.-]\d{2}[.-]\d{2})(?=\W|$)"
        match = re.search(pattern, filename)
        return match.group(1) if match else None

    def _extract_semantic_version(self, filename: str) -> str | None:
        """Extract semantic versions like '1.2.3' or 'v2.1.0'."""
        pattern = r"[vV]?(\d+\.\d+\.\d+(?:\.\d+)?)(?=[-._\s]|$)"
        match = re.search(pattern, filename)
        return match.group(1) if match else None

    def _extract_two_part_version(self, filename: str) -> str | None:
        """Extract two-part versions like '1.2' or 'v3.4'."""
        pattern = r"[vV]?(\d+\.\d+)(?=[-._\s]|$)"
        match = re.search(pattern, filename)
        return match.group(1) if match else None

    def _extract_single_number_version(self, filename: str) -> str | None:
        """Extract single number versions."""
        pattern = r"[vV]?(\d+)(?=[-._\s]|$)"
        match = re.search(pattern, filename)
        return match.group(1) if match else None
