# Changelog

All notable changes to AppImage Updater will be documented in this file.

## [Unreleased] - 2025-09-05

### 🏗️ Code Quality & Refactoring
- **REFACTORED**: Reduced code complexity in main.py functions
  - Broke down `_get_files_info()` function (complexity 11→8) into smaller helper functions:
    - `_find_matching_appimage_files()` for file discovery and error handling
    - `_format_file_groups()` for file group formatting
    - `_format_single_file_info()` for individual file information formatting
  - Broke down `_get_configuration_info()` function (complexity C→8) into focused helpers:
    - `_get_basic_config_lines()` for basic configuration display
    - `_add_optional_config_lines()` for prerelease and symlink path options
    - `_add_checksum_config_lines()` for checksum configuration
    - `_add_rotation_config_lines()` for file rotation configuration
  - Broke down `_remove_from_config_directory()` function (complexity C→6) into:
    - `_process_config_file_for_removal()` for individual config file processing
    - `_update_or_remove_config_file()` for file updates and removal
  - **IMPACT**: All functions now meet complexity standards (≤10 cyclomatic complexity)
  - **BENEFIT**: Improved code maintainability, readability, and testability

- **FIXED**: Code formatting and type annotation issues
  - Removed whitespace from blank lines (fixed 10+ W293 violations)
  - Fixed unused variable warning (B007) in `_group_files_by_rotation()`
  - Added proper type annotation for `rotation_groups` variable
  - **RESULT**: All ruff linting checks now pass
  - **RESULT**: All mypy type checks now pass
  - **RESULT**: All radon complexity checks now pass

### 🐛 Bug Fixes
- **FIXED**: Symlink detection for AppImage files with suffixes
  - Fixed `_get_valid_symlink_target()` function to properly detect symlinks pointing to files with suffixes like `.current` and `.old`
  - Changed condition from `target.name.endswith(".AppImage")` to `".AppImage" in target.name` to handle suffixed files
  - Resolves issue where symlinks pointing to rotation files (e.g., `app.AppImage.current`) were not detected
  - Now correctly displays symlinks in the `show` command for applications using file rotation systems

- **ENHANCED**: Symlink search paths aligned with go-appimage's appimaged
  - Updated symlink detection to use the same search paths as go-appimage's `appimaged` daemon
  - **Search locations now include**: `/usr/local/bin`, `/opt`, `~/Applications`, `~/.local/bin`, `~/Downloads`, plus all `$PATH` directories
  - **Improved compatibility**: Better integration with existing AppImage ecosystem tools
  - **Expanded coverage**: Finds symlinks in all standard AppImage locations used by the community

### 🆕 New Features
- **NEW**: `add` command for easy application configuration
  - **ADDED**: `appimage-updater add <name> <github_url> <download_dir>` for simple app addition
  - **INTELLIGENT**: Automatically generates regex patterns based on GitHub repository names
  - **SMART DEFAULTS**: Creates sensible configurations with checksum verification, daily updates, and proper file patterns
  - **FLEXIBLE**: Supports both single config files and directory-based configurations
  - **VALIDATED**: Ensures GitHub URLs and prevents duplicate application names
  - **USER-FRIENDLY**: Expands `~` paths and provides helpful success messages with next steps
  - **EXAMPLE**: `appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Applications/FreeCAD`

- **FIXED**: Type checking and linting errors in main.py
  - Resolved function name conflict between `list` command and Python's built-in `list` type
  - Renamed internal function from `list` to `list_apps` while keeping CLI command as `"list"`
  - Fixed deprecated `typing.List` imports, replaced with modern lowercase `list` annotations
  - Removed whitespace on blank lines and fixed line length violations
  - All mypy type checking errors resolved (26 errors → 0 errors)
  - All ruff linting errors fixed (7 errors → 0 errors)
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

### 🆕 New Features
- **NEW**: `show` command for detailed application information
  - **ADDED**: `appimage-updater show --app <name>` command to display comprehensive app details
  - **DISPLAYS**: Configuration settings (source, URL, download directory, patterns, frequency, checksum settings)
  - **SHOWS**: File information (size, modification time, executable status) for matching AppImage files
  - **DETECTS**: Symlinks pointing to AppImage files with status validation
  - **SUPPORTS**: Same configuration options as other commands (`--config`, `--config-dir`)
  - **INCLUDES**: Rich formatted output with color-coded panels and status indicators
  - **HANDLES**: Missing directories, permission errors, and broken symlinks gracefully
  - **EXAMPLE**: `appimage-updater show --app FreeCAD --config-dir ~/.config/appimage-updater/`

- **ENHANCED**: `symlink_path` configuration support
  - **ADDED**: Optional `symlink_path` field in application configuration for explicit symlink management
  - **DISPLAYS**: Configured symlink path in `show` command configuration section
  - **DETECTS**: Configured symlinks in addition to automatically discovered ones
  - **SEARCHES**: Added `~/Applications` to default symlink search locations
  - **PREPARES**: Foundation for future download rotation improvements using explicit symlink paths
  - **EXAMPLE**: `"symlink_path": "~/Applications/FreeCAD.AppImage"` in configuration

### 🧪 Testing & Quality Assurance
- **ENHANCED**: Comprehensive test coverage for `show` command and symlink_path
  - Added 8 new end-to-end tests covering all `show` command functionality and symlink_path
  - Tests valid/invalid applications, case-insensitive matching, error handling
  - Tests missing directories, disabled applications, symlink detection
  - Tests file discovery, executable permissions, and display formatting
  - Tests configured symlink_path display and detection
  - Enhanced smoke test to verify `show` command availability
  - Total test count increased from 40 to 48 tests
  - Main module test coverage improved from 78% to 79%

- **ENHANCED**: Comprehensive test coverage for `list` command
  - Added 8 new end-to-end tests covering all `list` command functionality
  - Tests single and multiple application configurations
  - Tests enabled/disabled status display and counting
  - Tests config file vs config directory loading
  - Tests error handling (missing files, invalid JSON)
  - Tests table formatting and path truncation features
  - Tests frequency unit display validation
  - Enhanced smoke test to verify `list` command availability
  - Total test count increased from 32 to 40 tests
  - Main module test coverage improved from 57% to 72%

- **IMPROVED**: Development workflow quality checks
  - Added `format` task to beginning of `check` task in Taskfile.yml
  - Code formatting now runs automatically before type checking and linting
  - Prevents formatting-related linting errors in CI/CD pipeline

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
- **NEW**: `list` command for viewing configured applications
  - **ADDED**: `appimage-updater list` command to display all configured applications
  - **DISPLAYS**: Application name, enabled/disabled status, source repository, download directory, and update frequency
  - **SUPPORTS**: Same configuration options as other commands (`--config`, `--config-dir`)
  - **SHOWS**: Summary with total applications and enabled/disabled counts
  - **EXAMPLE**: `appimage-updater list --config-dir ~/.config/appimage-updater/apps`

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
