# Changelog

All notable changes to AppImage Updater will be documented in this file.

## [Unreleased] - 2025-09-04

### 🐛 Bug Fixes
- **FIXED**: Pattern matching for existing AppImage files with suffixes
  - Updated application patterns to match files ending with `.AppImage.save`, `.AppImage.current`, `.AppImage.old`
  - Fixed FreeCAD pattern to handle case-insensitive extensions (both `.AppImage` and `.appimage`)
  - Fixed OrcaSlicer pattern to be more flexible with versioned assets
  - Resolved issue where all applications showed "Update available" with "Current: None"
  - Now correctly detects existing versions: `FreeCAD 1.0.2`, `FreeCAD_weekly 2025.09.03`, `OrcaSlicer 2.3.0`

- **FIXED**: Version comparison logic for releases with extra text
  - Enhanced version extraction to handle GitHub release names with non-version text
  - Fixed false positive updates for releases like "Development Build weekly-2025.09.03"
  - Version comparison now correctly extracts and compares just the version portion

### 🔧 Configuration Updates
- **IMPROVED**: Pattern matching precision for AppImage files with suffixes
  - **CHANGED**: Updated suffix patterns from `(\..*)?` to `(\.(|current|old))?` for better control
  - **PREVENTS**: Backup files (`.save`, `.backup`, `.bak`) from interfering with version detection
  - **MAINTAINS**: Support for rotation system files (`.current`, `.old`) and base AppImage files
  - **EXAMPLE**: `OrcaSlicer_Linux_AppImage_Ubuntu2404_.*\.AppImage(\.(|current|old))?$`
  - **RESOLVES**: False version detection from backup files causing incorrect "update available" status

- **CHANGED**: Application pattern configurations to support file suffixes
  - FreeCAD: `.*Linux-x86_64.*\.[Aa]pp[Ii]mage(\..*)?$`
  - FreeCAD_weekly: `FreeCAD_weekly.*Linux-x86_64.*\.AppImage(\..*)?$`
  - OrcaSlicer_nightly: `OrcaSlicer_Linux_AppImage_Ubuntu2404_.*\.AppImage(\.(|current|old))?$`

- **FIXED**: pytest-cov coverage conflicts in task check
  - Added `--no-cov` flag to `test:e2e` task to prevent coverage database conflicts
  - Configured `parallel = false` to avoid SQLite database conflicts during test runs
  - Added `--cov-config=pyproject.toml` for consistent coverage configuration
  - Fixes "FileNotFoundError: No such file or directory" errors during coverage combining

### 🛠️ Development & Testing
- **FIXED**: Test failures with missing trio dependency
  - Added `trio` as development dependency to support anyio pytest plugin backends
  - Resolves "ModuleNotFoundError: No module named 'trio'" in rotation tests
  - All parametrized tests now run successfully with both asyncio and trio backends
  - Added trio dependencies: trio==0.30.0, attrs==25.3.0, outcome==1.3.0.post0, sortedcontainers==2.4.0

- **ENHANCED**: Taskfile with additional test tasks
  - `task test:e2e` - Run end-to-end tests (without coverage to avoid conflicts)
  - `task test:e2e-coverage` - Run E2E tests with coverage reporting
  - `task test:smoke` - Quick smoke test for basic functionality validation
  - `task test:pattern-matching` - Test specific pattern matching functionality
  - `task test:all` - Run all tests including end-to-end validation

- **IMPROVED**: Documentation for testing and coverage
  - Updated WARP.md with comprehensive testing and coverage configuration section
  - Added troubleshooting steps for coverage database conflicts
  - Updated README.md with end-to-end testing commands

---

## [Previous] - 2025-01-04

### 🏗️ Code Quality
- **IMPROVED**: Significantly reduced code complexity across the codebase
  - Refactored `_check_updates` function from D complexity (critical) to B complexity
  - Broke down complex functions into smaller, focused methods
  - All functions now meet project complexity standards (≤10 cyclomatic complexity)
  - Enhanced maintainability and readability through better separation of concerns

- **FIXED**: MyPy type checking issues
  - Resolved import redefinition errors in `_version.py`
  - Fixed untyped function call issues in `config.py`
  - All 11 source files now pass strict type checking

### 🧹 Code Structure
- **REFACTORED**: Main update checking workflow
  - Extracted `_load_and_filter_config`, `_filter_apps_by_name`, `_perform_update_checks`
  - Separated update candidate processing and download handling
  - Clear separation between configuration, checking, and downloading phases

- **REFACTORED**: Download system architecture
  - Split `_download_single` into `_setup_download`, `_perform_download`, `_post_process_download`
  - Improved error handling and retry logic organization
  - Better separation of file download and checksum verification

- **REFACTORED**: Checksum verification system
  - Extracted `_parse_expected_checksum` and `_calculate_file_hash` methods
  - Simplified checksum parsing logic with dedicated functions
  - Enhanced GitHub checksum file association with pattern-based matching

- **REFACTORED**: User interface components
  - Separated successful and failed download result displays
  - Extracted checksum status indicator logic
  - Improved code organization for better maintainability

### 🔒 Security
- **NEW**: Automatic checksum verification for downloaded files
  - Supports SHA256, SHA1, and MD5 algorithms
  - Configurable checksum file patterns (e.g., `{filename}-SHA256.txt`)
  - Intelligent detection of checksum files in GitHub releases
  - Visual indicators for verification status in download results
  - Optional or required verification modes per application

### 🚀 Improvements
- **FIXED**: HTTP redirect handling for GitHub release downloads
  - Downloads now properly follow 302 redirects from GitHub CDN
  - Resolves previous "Redirect response '302 Found'" errors
  
- **ENHANCED**: Download robustness and reliability
  - Automatic retry logic with exponential backoff (up to 3 attempts)
  - Improved timeout configuration (separate connect/read/write timeouts)
  - Better error handling for network interruptions
  - Progress tracking with transfer speed and ETA

### 📝 Configuration
- **NEW**: Checksum configuration block for applications
  ```json
  "checksum": {
    "enabled": true,
    "pattern": "{filename}-SHA256.txt",
    "algorithm": "sha256", 
    "required": false
  }
  ```
- **NEW**: Application filtering with `--app` option
- **IMPROVED**: Debug logging with `--debug` flag for troubleshooting

### 🛠️ Developer Experience  
- Enhanced logging with checksum verification status
- Comprehensive debug information for download failures
- Better error messages and user feedback
- Updated documentation with security recommendations

### 📋 Technical Details
- Checksum files automatically downloaded and verified
- Support for multiple checksum file formats:
  - Hash + filename: `abc123... filename.AppImage`
  - Hash only: `abc123...`
  - Multiple files: One hash per line
- Configurable patterns support various naming conventions:
  - `{filename}-SHA256.txt` (FreeCAD style)
  - `{filename}_SHA256.txt` (underscore variant)  
  - `{filename}.sha256` (extension-based)

### 🧪 Tested With
- ✅ FreeCAD weekly builds (SHA256 verification)
- ✅ Large file downloads (>800MB) with retry logic
- ✅ GitHub release redirect handling
- ✅ Checksum pattern detection and parsing

---

## Contributing

This project follows [Semantic Versioning](https://semver.org/).
