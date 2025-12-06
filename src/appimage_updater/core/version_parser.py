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

    def generate_flexible_pattern_from_filename(self, filename: str, app_name: str | None = None) -> str:
        """Generate a flexible regex pattern from a filename by eliminating variable identifiers.

        The goal is to create a general pattern that matches the application name
        while being agnostic to architecture, distribution, version, and build type.

        Args:
            filename: The asset filename to generate pattern from
            app_name: Optional app name - if ends with release qualifiers (rc, alpha,
                      beta, weekly, nightly), include them in the pattern

        Pattern suffix (\\.(|current|old))?$ matches rotation suffixes for downloaded files.
        """
        # Start with the filename
        pattern = filename

        # Check if this is a zip-wrapped AppImage (affects extension pattern)
        has_zip = ".zip" in filename.lower()

        # Detect release type qualifier from app name (if provided)
        release_qualifier = self._detect_release_qualifier(app_name) if app_name else None

        # Remove file extension(s) to work with base name (handles .zip.AppImage too)
        base_name = re.sub(r"(\.zip)?\.AppImage$", "", pattern, flags=re.IGNORECASE)

        # Eliminate git commit hashes (6-8+ hex characters)
        # Match with any separator and followed by any non-word char or end
        base_name = re.sub(r"[-_][a-fA-F0-9]{6,12}(?=[-_.]|$)", "", base_name)

        # Eliminate architecture identifiers (with - or _ separator)
        arch_pattern = r"[-_](x86_64|x86-64|amd64|i386|i686|arm64|aarch64|armv7|armhf|X64|x64)(?=[-_.]|$)"
        base_name = re.sub(arch_pattern, "", base_name, flags=re.IGNORECASE)

        # Eliminate platform/OS identifiers (with - or _ separator)
        # Include optional build number suffix like linux1, linux2
        platform_pattern = r"[-_](linux\d*|win32|win64|windows|macos|darwin)(?=[-_.]|$)"
        base_name = re.sub(platform_pattern, "", base_name, flags=re.IGNORECASE)

        # Eliminate distribution identifiers (with - or _ separator)
        # Includes versioned distros like Ubuntu2404
        distro_pattern = r"[-_](fedora|ubuntu\d*|debian|centos|rhel|arch|manjaro|opensuse|appimage)(?=[-_.]|$)"
        base_name = re.sub(distro_pattern, "", base_name, flags=re.IGNORECASE)

        # Eliminate build type identifiers (nightly, weekly, daily, etc.)
        # These are stripped to create general patterns - differentiation between
        # stable/prerelease is done via the prerelease flag, not pattern matching
        build_types = r"nightly|weekly|daily|beta|alpha|dev|snapshot|test|debug|rc\d*|latest|stable|release"
        build_pattern = rf"[-_]({build_types})(?=[-_.]|$)"
        base_name = re.sub(build_pattern, "", base_name, flags=re.IGNORECASE)

        # Eliminate Python version identifiers (py311, py39, etc.)
        base_name = re.sub(r"[-_]py\d+(?=[-_.]|$)", "", base_name, flags=re.IGNORECASE)

        # Eliminate version numbers - handle multiple formats:
        # -v02.04.00.70, -1.0rc2, _V2.3.1, -928, etc.
        # Be aggressive: match versions with - or _ prefix
        # Order matters: more specific patterns first
        version_patterns = [
            r"[-_]v?\d+\.\d+\.\d+\.\d+",  # 4-part: v02.04.00.70
            r"[-_]v?\d+\.\d+\.\d+(?:rc\d*|beta\d*|alpha\d*)?",  # 3-part with optional suffix
            r"[-_]v?\d+\.\d+(?:rc\d*|beta\d*|alpha\d*)?",  # 2-part with optional suffix: 1.0rc2
            r"[-_]\d{3,}(?=[-_.]|$)",  # Build numbers: -928
        ]
        for vp in version_patterns:
            base_name = re.sub(vp, "", base_name, flags=re.IGNORECASE)

        # Clean up any double separators or trailing separators
        base_name = re.sub(r"[-_]+", "-", base_name)
        base_name = base_name.strip("-_")

        # Create flexible pattern that matches the cleaned base name with any suffixes
        # - No ^ anchor for flexibility in matching
        # - Include release qualifier pattern if app name indicates specific release type
        # - Include .zip extension if source had zip assets
        # - Always include rotation suffix pattern for downloaded file matching
        escaped_base = re.escape(base_name)
        # Make hyphens and underscores flexible - match either separator or none
        # This handles variations like "Bambu-Studio" vs "Bambu_Studio" vs "BambuStudio"
        escaped_base = re.sub(r"\\[-_]", "[-_]?", escaped_base)
        # Qualifier pattern includes .* after to allow content between qualifier and extension
        # e.g., FreeCAD_weekly-2025.12.03-Linux-x86_64.AppImage needs .*[Ww]eekly.*
        qualifier_pattern = release_qualifier + ".*" if release_qualifier else ".*"
        ext_pattern = r"\.(zip|AppImage)" if has_zip else r"\.AppImage"
        return f"(?i){escaped_base}{qualifier_pattern}{ext_pattern}(\\.(|current|old))?$"

    # Release qualifier patterns: (app_name_pattern, output_regex_pattern)
    # Separator is optional to handle both "OrcaSlicerRC" and "freecad_rc"
    _RELEASE_QUALIFIER_PATTERNS: list[tuple[str, str]] = [
        (r"[_-]?rc\d*$", ".*[Rr][Cc][0-9]+"),  # RC (release candidate)
        (r"[_-]?alpha\d*$", ".*[Aa]lpha"),  # Alpha
        (r"[_-]?beta\d*$", ".*[Bb]eta"),  # Beta
        (r"[_-]?weekly$", ".*[Ww]eekly"),  # Weekly
        (r"[_-]?nightly$", ".*[Nn]ightly"),  # Nightly
    ]

    def _detect_release_qualifier(self, app_name: str) -> str | None:
        """Detect release type qualifier from app name and return corresponding regex pattern.

        Args:
            app_name: The application name to check

        Returns:
            Regex pattern for the qualifier, or None if no qualifier detected
        """
        app_lower = app_name.lower()
        for pattern, result in self._RELEASE_QUALIFIER_PATTERNS:
            if re.search(pattern, app_lower):
                return result
        return None

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
