"""Unit tests for VersionChecker class."""

from appimage_updater.core.version_checker import VersionChecker


class TestVersionChecker:
    """Test cases for VersionChecker class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.version_checker = VersionChecker()

    def test_file_matches_app_direct_match(self) -> None:
        """Test direct filename matching."""
        assert self.version_checker._file_matches_app("freecad.appimage", "freecad")
        assert self.version_checker._file_matches_app("openshot.appimage", "openshot")
        assert self.version_checker._file_matches_app("gimp_2.10.appimage", "gimp")

    def test_file_matches_app_studio_pattern(self) -> None:
        """Test Studio -> _Studio pattern matching."""
        assert self.version_checker._file_matches_app(
            "bambu_studio_ubuntu-24.04_pr-8184.appimage", "bambustudio"
        )

    def test_file_matches_app_suffix_patterns(self) -> None:
        """Test suffix pattern matching - handles Nightly, RC, Beta, etc."""
        # OrcaSlicerNightly -> OrcaSlicer pattern (the original bug we fixed)
        assert self.version_checker._file_matches_app(
            "orcaslicer_linux_appimage_ubuntu2404_nightly.appimage.current",
            "orcaslicernightly"
        )
        # OrcaSlicerRC -> OrcaSlicer pattern (the new case)
        assert self.version_checker._file_matches_app(
            "orcaslicer_linux_appimage_ubuntu2404_v2.3.1-beta.appimage.current",
            "orcaslicerrc"
        )
        # Generic patterns for other suffixes
        assert self.version_checker._file_matches_app(
            "someapp_linux_build.appimage", "someappbeta"
        )
        assert self.version_checker._file_matches_app(
            "testapp_dev_build.appimage", "testappalpha"
        )

    def test_file_matches_app_negative_cases(self) -> None:
        """Test cases that should not match."""
        assert not self.version_checker._file_matches_app(
            "gimp_2.10.appimage", "inkscape"
        )
        assert not self.version_checker._file_matches_app(
            "otherapp_nightly.appimage", "orcaslicernightly"
        )
