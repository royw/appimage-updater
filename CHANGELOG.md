# Changelog

All notable changes to AppImage Updater will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- implement dynamic version injection for documentation (43717ff)

- Add fix command with orphaned .current.info file cleanup (a203a8d)

- support show --add-command path flags with full test coverage (1aa964f)

### Changed
- enhance getting-started guide with comprehensive path resolution and real-world examples (4aee99e)

- reduce cyclomatic complexity in command and display modules (0bb7d16)
- reduce cyclomatic complexity by extracting helper methods (a07de4b)

### Fixed
- show graceful error message for wildcard expansion without quotes (e180828)

- resolve e2e test import error (494c526)
- partially address conftest linting issues (9bea216)
- eliminate async warnings in e2e tests (da253df)
- resolve e2e test HTTP mocking issues (34e1ed5)

## [0.5.4] - 2025-11-30

### Added

### Changed

### Fixed

- preserve rc prerelease suffix in version normalization (b4ee937)

## [0.5.3] - 2025-11-06

### Added

### Changed

- rename release:build to release:prepare for clarity (8f94640)

### Fixed

- call root make task from release:prepare using :make syntax (f9f052a)

## [0.5.3] - 2025-11-06

### Added

### Changed

### Fixed

## [0.5.3] - 2025-11-06

### Added

### Changed

### Fixed

## [0.5.3] - 2025-11-06

### Added

### Changed

### Fixed

- remove compact mapping syntax from all Taskfiles to prevent YAML parsing errors (12907a8)

## [0.5.3] - 2025-11-06

### Added

### Changed

- fix LaTeX escaping in README.md (fdb6b5d)

### Fixed

- update workflow configuration for new release process (1e3fcab)

## [0.5.2] - 2025-10-16

## [0.5.2] - 2025-10-16

### Added

- **show --add-command Enhancement**: Added newline after each command for better readability
- **Documentation Improvements**: Added more real-world application examples from show --add-command

### Changed

- **PyPI Publishing Workflow**: Added required contents:read permission for trusted publishing
- **PyPI Publishing Setup Guide**: Enhanced with practical workflow instructions and testpypi workflow
- **Documentation**: Updated all version references to 0.5.2
- **Documentation**: Fixed bare URLs to use angle brackets for markdown compliance

## [0.5.1] - 2025-10-15

### Changed

- **PyPI Publishing Preparation**
  - Enhanced PyPI metadata with keywords for better discoverability
  - Added project URLs (homepage, documentation, repository, issues, changelog)
  - Updated classifiers to Beta status with appropriate audience targeting
  - Updated LICENSE copyright to 2025 Roy Wright
  - Version bumped to 0.5.1 for PyPI publication
  - Updated all documentation version references to 0.5.1

## [0.5.0] - 2025-01-15

### Release Notes

This is the initial public release of AppImage Updater - a comprehensive tool for managing AppImage applications with automatic updates, file rotation, checksum verification, and multi-repository support.

## [0.4.20] - 2025-10-15

### Changed

- **Massive complexity reduction - eliminated all high-complexity functions**

  - Reduced 20 B-rated functions to 7 (65% reduction)
  - Eliminated all C-rated functions (3 total)
  - Eliminated all B-10 functions (2 total)
  - Eliminated all B-9 functions (3 total)
  - Eliminated all B-8 functions (6 total)
  - Eliminated all B-7 functions (6 total)
  - Only 7 well-designed B-6 functions remaining
  - Extracted 30+ focused helper functions following single responsibility principle
  - Applied data-driven patterns (dictionary mappings, pattern lists)
  - Improved code organization with reusable helper methods
  - Better testability through smaller, single-purpose functions
  - All 2083 tests passing with 74% code coverage maintained

- **Eliminated code smell by removing test-only code from production**

  - Removed `create_silent_http_logger()` factory function (unused trivial wrapper)
  - Removed `create_verbose_http_tracker()` factory function (never used in codebase)
  - Moved `SilentHTTPLogger` class from `src/` to `tests/unit/instrumentation/test_helpers.py`
  - Cleaner separation between production and test code
  - Simpler API with only actually-used factory functions
  - Test utilities properly located in test directories

- **Protected README.md LaTeX syntax from mdformat processing**

  - Excluded README.md from `task format:markdown` to preserve `$$\color{}` syntax
  - Excluded README.md from `task lint:markdown` to avoid linting issues
  - Created `.mdformat-exclusions.md` documenting exclusion rationale
  - LaTeX-rendered colored text in tables now preserved during formatting

- **Major output formatter refactoring for improved type safety and code quality**

  - `get_output_formatter()` now guarantees a valid formatter or raises `RuntimeError`
  - Changed return type from `Any` to `OutputFormatter` for compile-time type checking
  - Eliminated ~30 defensive None checks across 14 files
  - Removed ~230 lines of dead code and ~37 obsolete tests
  - Simplified command execution by removing duplicate code paths
  - All code now enforces formatter availability through `OutputFormatterContext`
  - Improved maintainability with fail-fast error detection

- **Type annotation improvements - replaced `Any` with proper types**

  - Fixed 9 functions with vague `Any` return types to use specific types
  - Config loading functions now return `Config` instead of `Any`
  - Repository functions now return `RepositoryClient` instead of `Any`
  - Table creation functions now return `Table` instead of `Any`
  - Improved IDE autocomplete and compile-time type checking
  - Better code documentation through explicit type contracts
  - Zero MyPy errors maintained

- **Package architecture cleanup - enforced "no code in \_\_init\_\_.py" principle**

  - Cleaned up 6 `__init__.py` files to contain only docstrings
  - Removed ~80 lines of imports and `__all__` declarations
  - Updated imports to use direct module paths instead of package imports
  - Added `lint:packages` task to enforce this principle going forward
  - All package files now follow clean architecture boundaries

- **Improved markdown output formatting**

  - URLs now wrapped in angle brackets (`<URL>`) for better markdown compatibility
  - Removed "ℹ INFO: " prefix from info messages for cleaner output
  - Enhanced `tree-to-github-markdown.sh` script:
    - Uses dash bullets (`-`) instead of asterisks (`*`)
    - Proper even indentation (0, 2, 4 spaces)
    - Adds blank line after path for better readability
    - Removes markdown link formatting from symlinks
    - Bold header format instead of H1

### Added

- **New lint task: `lint:packages`**
  - Verifies all `src/**/__init__.py` files only contain docstrings
  - Uses Python AST parsing to detect code violations
  - Integrated into main `lint` task for automatic checking
  - Enforces clean package architecture

### Fixed

- **Consistent home path display across all formatters**
  - Home directory now replaced with `~` in all output formats (rich, plain, markdown, json, html)
  - Previously only Rich formatter performed this substitution
  - Moved path replacement logic to data preparation layer for consistency

### Removed

- **Dead code elimination**
  - Removed 19 unused functions across multiple modules
  - Removed fallback console.print() calls (formatter now always available)
  - Removed duplicate command execution methods (\_execute_with_formatter_context, \_execute_without_formatter)
  - Removed obsolete display_check_results and related helper functions
  - Cleaned up 7 unused imports
  - Removed test_table_formatting.py (entire obsolete test file)

## [0.4.19] - 2025-10-14

### Added

- **Colorized config commands** for improved readability
  - `config list`: Colored output in both Rich and Markdown formats
    - Setting names displayed in cyan
    - Valid values displayed in dim/gray
    - Examples displayed in green
    - Markdown format uses LaTeX color syntax for GitHub rendering
  - `config show`: Now uses output formatter's console for consistent colors
  - `config show-effective`: Now uses output formatter's console for consistent colors
- **Test infrastructure improvements**
  - Added `test:_check` task to detect misplaced config.json in apps/ directory
  - Runs after all pytest commands to catch tests writing to real config directory
  - Prevents config pollution with clear error messages and removal instructions
- **Tree-to-markdown utility script**
  - Added `scripts/tree-to-github-markdown.sh` for converting tree output to GitHub markdown
  - Supports colored output using LaTeX syntax
  - Properly escapes special characters for markdown rendering

### Changed

- **Improved code maintainability** by reducing function complexity
  - Extracted helper methods in markdown formatter (5 new methods)
  - Extracted helper methods in plain formatter (5 new methods)
  - All functions now pass complexity lint checks (under threshold of 10)

### Fixed

- **Consistent function naming** across codebase
  - Renamed `list_available_settings` → `list_settings`
  - Renamed `get_checksum_status` → `_get_checksum_verification_status`
  - Updated all tests to match new function signatures
- **Test fixes**
  - Fixed logging interface test after info→debug change
  - Fixed RuntimeWarnings about unawaited coroutines in mock responses
  - Fixed whitespace warnings in test files

### Documentation

- **README improvements**
  - Replaced non-rendering inline HTML with properly formatted markdown
  - Used LaTeX color syntax for tree output, tables, and status displays
  - Added colored markdown tables for application lists and check results
  - Improved readability with structured sections and proper formatting
  - All output examples now render correctly on GitHub
- **Formatter audit complete**
  - Completed comprehensive audit of all CLI commands and display functions
  - Verified all 13 commands properly use output formatter system
  - Documented acceptable module-level console usage patterns
  - All verification steps passed (console usage, formatter support, color output, tests)

## [0.4.18] - 2025-10-14

### Added

- **Enhanced version:bump task** with changelog validation and automation
  - Validates CHANGELOG.md has [Unreleased] section with content
  - Displays current unreleased changes for user review
  - Prompts user to confirm changelog is complete before proceeding
  - Automatically updates CHANGELOG.md: moves [Unreleased] to new version with date
  - Commits both pyproject.toml and CHANGELOG.md together
  - POSIX-compliant shell implementation (works in sh, bash, zsh)
  - Prevents accidental releases with incomplete or empty changelogs

### Documentation

- **COMPLETE**: Comprehensive documentation review and updates
  - Fixed all configuration examples to use directory-based structure
  - Updated all version numbers to 0.4.17
  - Removed references to deleted `init` command
  - Fixed CLI option documentation (removed duplicates and non-existent options)
  - Updated automation examples (cron, systemd)
  - Verified 21 documentation files for accuracy

## [0.4.17] - 2025-01-14

### Breaking Changes

- **REMOVED**: Single-file configuration format support
  - All configurations must now use directory-based structure: `~/.config/appimage-updater/apps/`
  - Global config in `~/.config/appimage-updater/config.json`
  - Each application in separate file: `~/.config/appimage-updater/apps/<appname>.json`
- **REMOVED**: `--config` CLI option (replaced with `--config-dir` and `--config-file`)
  - Use `--config-dir` to specify configuration directory
  - Use `--config-file` for specific application config files

### Added

- **Auto-initialization**: Configuration directory created automatically on first run
- **Improved error messages**: Better user feedback for missing configurations
- **Debug logging**: Reduced noise from auto-init messages (INFO → DEBUG)

### Fixed

- **Configuration loading**: Proper `global_config` wrapper in config.json
- **Global config**: Correctly loads from config.json when using apps/ directory
- **Stack trace handling**: All tests properly use temp directories

### New Features

- **User Experience**: Help Messages Instead of Errors for Missing Arguments

  - **PROBLEM SOLVED**: Commands now show helpful usage information instead of cryptic error messages when required arguments are missing
  - **IMPROVED UX**: Follows modern CLI patterns used by tools like `git`, `docker`, and `kubectl`
  - **COMMANDS ENHANCED**:
    - `appimage-updater config` - Shows help when ACTION argument is missing
    - `appimage-updater show` - Shows help when APP_NAMES argument is missing
    - `appimage-updater edit` - Shows help when APP_NAMES argument is missing
    - `appimage-updater remove` - Shows help when APP_NAMES argument is missing
  - **BEFORE/AFTER EXAMPLE**:
    - Before: `appimage-updater config` → "Error: Missing argument 'ACTION'"
    - After: `appimage-updater config` → Shows complete usage help with examples and options
  - **USER BENEFITS**:
    - No need to remember to add `--help` when exploring commands
    - Immediate access to usage information and examples
    - Reduced friction for new users learning the CLI
    - More discoverable and user-friendly interface
  - **TECHNICAL**: Preserved all existing functionality when arguments are provided

- **MAJOR**: Multi-App CLI Operations Support

  - **PROBLEM SOLVED**: Users can now operate on multiple applications simultaneously instead of one at a time
  - **MULTIPLE APP NAMES**: All commands (`check`, `show`, `edit`, `remove`) now accept multiple application names
  - **GLOB PATTERN SUPPORT**: Use patterns like `"Orca*"` or `"*Studio"` to match multiple applications by name
  - **CASE-INSENSITIVE**: All application name matching is case-insensitive for better usability
  - **BATCH OPERATIONS**: Perform bulk operations efficiently:
    - `appimage-updater check FreeCAD VSCode OrcaSlicer` - check multiple apps
    - `appimage-updater edit "Test*" --disable` - disable all test applications
    - `appimage-updater remove "Old*" --force` - remove all old applications
    - `appimage-updater show App1 App2 App3` - show details for multiple apps
  - **INTELLIGENT ERROR HANDLING**: Clear reporting of found vs. not-found applications
  - **BACKWARD COMPATIBLE**: Single app usage continues to work exactly as before
  - **CLI ENHANCEMENTS**:
    - Updated command signatures to accept multiple `APP_NAMES...` arguments
    - Enhanced help text with glob pattern examples
    - Consistent behavior across all multi-app commands
  - **ARCHITECTURE**:
    - New `_filter_apps_by_names()` function for multi-app filtering
    - Enhanced `_filter_apps_by_single_name()` with glob pattern support using `fnmatch`
    - Unified error handling and user feedback for missing applications
  - **TESTING**: 17 comprehensive tests covering all multi-app scenarios:
    - Multiple app names with mixed existing/non-existing apps
    - Glob pattern matching and case-insensitive operations
    - Error handling and exit codes for various scenarios
    - Integration with all CLI commands (check, show, edit, remove)

- **MAJOR**: Automatic ZIP File Extraction Support

  - **PROBLEM SOLVED**: Applications like BambuStudio that distribute AppImages inside ZIP files now work seamlessly
  - **ZERO-CONFIG**: ZIP files are automatically detected and extracted with no configuration needed
  - **INTELLIGENT**: Scans ZIP contents for `.AppImage` files and extracts them to download directory
  - **CLEANUP**: Original ZIP file is automatically removed after successful extraction
  - **MULTI-FILE**: Handles ZIP files with multiple AppImages (uses first found, logs warning)
  - **SUBDIRECTORY SUPPORT**: Extracts AppImages from subdirectories within ZIP files
  - **ERROR HANDLING**: Clear error messages for invalid ZIP files or missing AppImages
  - **FULL INTEGRATION**: Works seamlessly with:
    - File rotation and symlink management
    - Checksum verification (applied to extracted AppImage)
    - Version metadata creation (`.info` files for extracted AppImage)
    - Progress tracking and retry logic
  - **EXAMPLES**:
    - **BambuStudio**: `appimage-updater add BambuStudio https://github.com/bambulab/BambuStudio ~/Apps/BambuStudio`
    - **Pattern Support**: `"(?i)Bambu_?Studio_.*\\.(zip|AppImage)(\\.(|current|old))?$"` for both formats
  - **ARCHITECTURE**:
    - New `_extract_if_zip()` method in `Downloader` class
    - Post-download processing pipeline automatically handles ZIP extraction
    - Updates `candidate.download_path` to point to extracted AppImage for downstream processing
  - **TESTING**: 14 comprehensive tests covering all scenarios:
    - Successful extraction from ZIP files
    - Multiple AppImages (uses first, warns)
    - No AppImages found (clear error)
    - Invalid ZIP files (error handling)
    - Non-ZIP files (skipped)
    - Subdirectories in ZIP
    - Directory entries ignored

- **MAJOR**: Direct Download URL Support with `--direct` Option

  - **PROBLEM SOLVED**: Ambiguity in URL-based repository detection for direct download URLs (nightly builds, CI artifacts)
  - **EXPLICIT CONTROL**: New `--direct` flag allows users to explicitly mark URLs as direct downloads
  - **BYPASSES DETECTION**: When `--direct` is used, skips URL pattern-based repository type detection
  - **REPOSITORY FACTORY**: Enhanced `get_repository_client()` to accept explicit `source_type` parameter
  - **VERSION CHECKER**: Updated to use `source_type` from configuration instead of URL detection
  - **CLI INTEGRATION**: Available in both `add` and `edit` commands with consistent behavior
  - **CONFIGURATION**: Sets `source_type: "direct"` in application configuration when flag is used
  - **BACKWARD COMPATIBLE**: Existing configurations continue working with URL detection fallback
  - **EXAMPLES**:
    - `appimage-updater add --direct NightlyBuild https://nightly.example.com/app.AppImage ~/Apps/NightlyBuild`
    - `appimage-updater edit MyApp --direct --url https://ci.example.com/artifacts/latest.AppImage`
  - **USE CASES**:
    - Nightly builds from CI systems
    - Direct download URLs that don't follow GitHub repository patterns
    - Custom download endpoints
    - Any URL where repository detection might be ambiguous
  - **TECHNICAL DETAILS**:
    - Maps `"direct"` source type to `DirectDownloadRepository` client
    - Supports `"github"`, `"direct_download"`, `"dynamic_download"`, and `"direct"` source types
    - Maintains existing URL detection as fallback when no explicit source type provided
  - **DOCUMENTATION**: Comprehensive updates to usage.md, getting-started.md, and WARP.md with examples and explanations

### Bug Fixes

- **FIXED**: Version checker now searches multiple releases for pattern matches

  - **PROBLEM**: Applications with non-standard release patterns (like nightly builds) failed when the latest release didn't contain matching assets
  - **SOLUTION**: Enhanced `_check_repository_updates()` to search through up to 20 releases instead of just the latest one
  - **RESULT**: Finds the first release with assets matching the specified pattern, regardless of publication date
  - **USE CASE**: Fixes issues with continuous nightly builds where the "nightly-builds" release isn't the most recent by date
  - **EXAMPLE**: OrcaSlicer nightly builds now work correctly with pattern `.*nightly.*\.(zip|AppImage)$`
  - **PERFORMANCE**: Efficient early-exit when matching release is found
  - **BACKWARD COMPATIBLE**: Standard versioned releases continue working as before

- **FIXED**: AppImage rotation naming issue for extracted ZIP files

  - **PROBLEM**: Rotation suffix (`.current`, `.old`) was incorrectly added before `.AppImage` extension
  - **SOLUTION**: Modified rotation logic to treat `.AppImage` as part of the base filename
  - **RESULT**: Rotation suffixes now correctly added after `.AppImage` (e.g., `filename.AppImage.current`)
  - **CONSISTENCY**: Ensures consistent naming for both directly downloaded and ZIP-extracted AppImages
  - **TESTING**: Updated rotation tests to verify correct naming format
  - **BACKWARD COMPATIBLE**: Handles both naming styles during version detection

______________________________________________________________________

## [0.2.0] - 2025-01-09

### 🆕 New Features

- **NEW**: `check` command now supports optional positional argument for application name

  - **USAGE**: `appimage-updater check [app-name]` instead of `--app` option
  - **BACKWARD COMPATIBLE**: Still supports all existing `check` command functionality
  - **EXAMPLE**: `appimage-updater check GitHubDesktop` to check a specific application
  - **FLEXIBLE**: Can be used with or without the application name argument

- **NEW**: Automatic GitHub URL normalization in `add` command

  - **INTELLIGENT**: Automatically detects and converts GitHub download URLs to repository URLs
  - **USER-FRIENDLY**: Warns users when URL correction is applied with clear feedback
  - **PREVENTS ERRORS**: Fixes common mistake of providing release download links instead of repo URLs
  - **EXAMPLES**: Converts `https://github.com/user/repo/releases/download/...` → `https://github.com/user/repo`
  - **EXAMPLES**: Converts `https://github.com/user/repo/releases` → `https://github.com/user/repo`

### Configuration Fixes

- **FIXED**: GitHubDesktop configuration URL corrected from invalid release download URL to proper repository URL
- **FIXED**: GitHubDesktop configuration removed invalid rotation settings that were causing configuration errors

### Testing & Quality Assurance

- **ENHANCED**: Added comprehensive tests for GitHub URL normalization
  - Tests normalization of release download URLs to repository URLs
  - Tests normalization of releases page URLs to repository URLs
  - Tests that valid repository URLs remain unchanged
  - Verified all existing tests continue to pass

### Configuration Updates

- **UPDATED**: Version bumped from 0.1.1 to 0.2.0 reflecting significant feature additions

______________________________________________________________________

## [Previous] - 2025-01-04

### BUILD Code Quality

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

### LOCK Security

- **NEW**: Automatic checksum verification for downloaded files
  - Supports SHA256, SHA1, and MD5 algorithms
  - Configurable checksum file patterns (e.g., `{filename}-SHA256.txt`)
  - Intelligent detection of checksum files in GitHub releases
  - Visual indicators for verification status in download results
  - Optional or required verification modes per application

### DEPLOY Improvements

- **FIXED**: HTTP redirect handling for GitHub release downloads

  - Downloads now properly follow 302 redirects from GitHub CDN
  - Resolves previous "Redirect response '302 Found'" errors

- **ENHANCED**: Download robustness and reliability

  - Automatic retry logic with exponential backoff (up to 3 attempts)
  - Improved timeout configuration (separate connect/read/write timeouts)
  - Better error handling for network interruptions
  - Progress tracking with transfer speed and ETA

### COMMIT Configuration

- **NEW**: `list` command for viewing configured applications

  - **ADDED**: `appimage-updater list` command to display all configured applications
  - **DISPLAYS**: Application name, enabled/disabled status, source repository, download directory, and update frequency
  - **SUPPORTS**: Same configuration options as other commands (`--config-dir`)
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

### TOOLS Developer Experience

- Enhanced logging with checksum verification status
- Comprehensive debug information for download failures
- Better error messages and user feedback
- Updated documentation with security recommendations

### LIST Technical Details

- Checksum files automatically downloaded and verified
- Support for multiple checksum file formats:
  - Hash + filename: `abc123... filename.AppImage`
  - Hash only: `abc123...`
  - Multiple files: One hash per line
- Configurable patterns support various naming conventions:
  - `{filename}-SHA256.txt` (FreeCAD style)
  - `{filename}_SHA256.txt` (underscore variant)
  - `{filename}.sha256` (extension-based)

### TEST Tested With

- PASS FreeCAD weekly builds (SHA256 verification)
- PASS Large file downloads (>800MB) with retry logic
- PASS GitHub release redirect handling
- PASS Checksum pattern detection and parsing

______________________________________________________________________

## Contributing

This project follows [Semantic Versioning](https://semver.org/).

- **Security**: Read-only access to public repositories only - cannot access private data or modify anything

### TEST **Testing & Quality Assurance**

**Step-by-Step Token Creation**:

1. **Create Classic PAT (Recommended)**:

   - Visit: [GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)](https://github.com/settings/tokens)
   - Click "Generate new token (classic)"
   - Set token name: `AppImage-Updater`
   - Set expiration: Choose your preference (90 days, 1 year, or no expiration)
   - **Select ONLY**: `public_repo` (under "repo" section)
   - Click "Generate token"
   - **IMPORTANT**: Copy the token immediately (you won't see it again)

1. **Create Fine-grained PAT (Alternative)**:

   - Visit: [GitHub Settings > Developer settings > Personal access tokens > Fine-grained tokens](https://github.com/settings/personal-access-tokens/new)
   - Set token name: `AppImage-Updater`
   - Set expiration and resource access as desired
   - Under "Repository permissions":
     - **Contents**: `Read`
     - **Metadata**: `Read` (automatically selected)
   - Click "Generate token"

**Token Storage Options** (Choose one):

```bash
# Option 1: Environment Variable (Recommended)
export GITHUB_TOKEN="ghp_your_token_here"
# Add to ~/.bashrc or ~/.profile to persist

# Option 2: App-Specific Environment Variable
export APPIMAGE_UPDATER_GITHUB_TOKEN="ghp_your_token_here"

# Option 3: Plain Text Token File
echo "ghp_your_token_here" > ~/.appimage-updater-github-token
chmod 600 ~/.appimage-updater-github-token  # Secure permissions

# Option 4: JSON Token File
mkdir -p ~/.config/appimage-updater
echo '{"github_token": "ghp_your_token_here"}' > ~/.config/appimage-updater/github-token.json
chmod 600 ~/.config/appimage-updater/github-token.json

# Option 5: Global Config File
mkdir -p ~/.config/appimage-updater
echo '{
  "github": {
    "token": "ghp_your_token_here"
  }
}' > ~/.config/appimage-updater/config.json
chmod 600 ~/.config/appimage-updater/config.json
```

**Usage Examples**:

```bash
# All commands automatically use authentication when available
appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Apps/FreeCAD
appimage-updater check
appimage-updater list

# Debug mode shows authentication status
appimage-updater --debug add MyApp https://github.com/user/repo ~/Apps/MyApp
# Output: "GitHub API: Authenticated (5000 req/hour via GITHUB_TOKEN environment variable)"
```

**Security Features**:

- **Principle of Least Privilege**: Token only needs read access to public repositories
- **No Sensitive Data**: Cannot access private repos, user data, or organization information
- **Read-Only Operations**: Only fetches release information and download metadata
- **No Token Exposure**: Tokens never appear in logs or debug output
- **Priority Security**: Environment variables take precedence over files
- **File Permissions**: Supports secure file permissions (600) for token files

#### TEST **Testing & Quality Assurance**

- **COMPREHENSIVE**: 25 new tests covering all authentication scenarios
- **REAL-WORLD**: Tested with actual GitHub repositories and API responses
- **COVERAGE**: Token discovery, priority ordering, error handling, CLI integration
- **VALIDATED**: Works with both valid and invalid tokens, handles API failures gracefully
- **REGRESSION**: Ensures anonymous access continues working when no token available

#### 💡 **User Benefits**

- **ELIMINATES**: "Rate limit exceeded" errors during normal usage
- **IMPROVES**: Reliability of GitHub release fetching and pattern generation
- **ENHANCES**: User experience with faster, more reliable operations
- **FUTURE-PROOFS**: Supports any scale of AppImage management without API limits
- **MAINTAINS**: Full backward compatibility - works with or without authentication

### DEPLOY New Features

- **SEARCH MAJOR**: Automatic Prerelease Detection in `add` Command
  - **PROBLEM SOLVED**: Repositories with only prerelease versions (like continuous builds) now work seamlessly
  - **INTELLIGENT**: Automatically analyzes GitHub repository releases to detect prerelease-only repositories
  - **ZERO-CONFIG**: For repos like appimaged, automatically enables `prerelease: true` without user intervention
  - **SMART DETECTION**: Distinguishes between:
    - **Continuous builds** (only prereleases) → auto-enables prerelease support
    - **Stable releases** (has non-prereleases) → keeps prerelease disabled
    - **Mixed repositories** (both types) → defaults to stable releases only
  - **USER CONTROL**: Explicit `--prerelease` or `--no-prerelease` flags always override auto-detection
  - **GRACEFUL FALLBACK**: API failures (rate limits, network errors) default to `prerelease: false`
  - **VISUAL FEEDBACK**: Shows `SEARCH Auto-detected continuous builds - enabled prerelease support` when triggered
  - **EXAMPLES**:
    - `appimage-updater add appimaged https://github.com/probonopd/go-appimage ~/Apps/appimaged` → auto-enables prerelease
    - `appimage-updater add FreeCAD https://github.com/FreeCAD/FreeCAD ~/Apps/FreeCAD` → keeps prerelease disabled
  - **IMPACT**: Eliminates configuration errors for continuous build applications like appimaged
  - **TESTING**: 16 comprehensive tests covering all scenarios (prereleases-only, mixed, stable, API errors, user overrides)
  - **ARCHITECTURE**: Async implementation with proper error handling and rate limit resilience

### VERSION Technical Improvements

- **ENHANCED**: Async Architecture for GitHub API Integration
  - **REFACTORED**: Made `add` command fully async to support GitHub API calls during configuration generation
  - **FIXED**: Resolved coroutine warnings by creating async version of pattern generation (`_generate_appimage_pattern_async`)
  - **IMPROVED**: Better error handling and rate limit management in GitHub API interactions
  - **RESULT**: Clean async implementation with no runtime warnings

### TEST Quality Assurance

- **COMPREHENSIVE TESTING**: 16 new tests for automatic prerelease detection

  - **UNIT TESTS**: `_should_enable_prerelease()` function with all scenarios:
    - Repositories with only prereleases (PASS enables prerelease)
    - Repositories with stable releases (FAIL keeps disabled)
    - Mixed repositories (FAIL defaults to stable)
    - Empty repositories (FAIL safe default)
    - Draft-only releases (FAIL ignores drafts)
    - API failures (FAIL graceful fallback)
  - **INTEGRATION TESTS**: Full `add` command workflows:
    - Auto-detection with continuous build repos
    - No auto-detection with stable repos
    - User explicit flags override auto-detection
    - Configuration file validation
  - **REGRESSION TESTING**: All existing 116 tests continue to pass
  - **COVERAGE**: Maintained 76% test coverage across codebase

- **REAL-WORLD VALIDATION**: Tested with actual repositories

  - **probonopd/go-appimage**: Successfully auto-detects prerelease-only (continuous tag)
  - **FreeCAD/FreeCAD**: Correctly maintains stable release preference
  - **Rate limit handling**: Graceful fallback when GitHub API limits are exceeded

- **MAJOR**: Intelligent Pattern Generation from GitHub Releases

  - **PROBLEM SOLVED**: Fixed pattern generation issues where repository names didn't match actual file prefixes (e.g., OpenShot)
  - **NEW APPROACH**: `add` command now fetches actual GitHub releases to analyze real AppImage filenames
  - **SMART ANALYSIS**: Extracts common prefixes from actual files instead of guessing from repository names
  - **CASE-INSENSITIVE**: Generates `(?i)` patterns that work regardless of filename casing
  - **REAL-WORLD ACCURACY**: Patterns based on actual release data, not assumptions
  - **FALLBACK SAFE**: Falls back to old heuristic method if GitHub API is unavailable
  - **EXAMPLE**: For OpenShot (repo: `openshot-qt`, files: `OpenShot-v3.3.0-x86_64.AppImage`):
    - **OLD**: `openshot\-qt.*[Ll]inux.*\.AppImage` (FAIL doesn't match)
    - **NEW**: `(?i)OpenShot\-v3\..*\.AppImage` (PASS matches perfectly)
  - **IMPACT**: Dramatically improves accuracy for applications where repo names differ from file prefixes

### BUILD Build System

- **NEW**: `build` task for creating distribution packages
  - **ADDED**: `task build` command to create wheel and sdist packages using `uv build`
  - **INTEGRATED**: Runs full quality checks (`task check`) before building to ensure package quality
  - **AUTOMATED**: Cleans build artifacts before creating new packages
  - **FEEDBACK**: Provides clear build progress and completion messages with package listing
  - **OUTPUT**: Creates both wheel (`.whl`) and source distribution (`.tar.gz`) in `dist/` directory
  - **USAGE**: `task build` - Build distribution packages ready for PyPI or local installation

### DEPLOY CI/CD & GitHub Actions - COMPLETE SUCCESS

- **NEW**: Full GitHub Actions CI/CD pipeline with automated deployment

  - **ADDED**: `docs.yml` workflow for automated GitHub Pages deployment
    - **LIVE DOCUMENTATION**: Successfully deployed at `https://royw.github.io/appimage-updater/`
    - **AUTO-DEPLOYMENT**: Updates automatically on every push to main branch
    - **ENHANCED NAVIGATION**: Home icons (🏠), clickable headers, keyboard shortcuts (Alt+H)
    - **PROFESSIONAL THEME**: Material design with dark/light mode toggle
    - **FEATURES**: Strict MkDocs build, fast `uv` dependency installation
    - **TRIGGERS**: Push to main, PRs, manual dispatch
  - **ADDED**: `ci.yml` workflow for comprehensive testing and package building
    - **MATRIX TESTING**: Tests on Python 3.11 and 3.12
    - **QUALITY GATES**: Formatting, linting, type checking, complexity analysis
    - **COVERAGE**: Automated coverage reporting with Codecov integration (optional)
    - **BUILD ARTIFACTS**: Stores built packages for distribution
    - **PYPI PUBLISHING**: Ready for automated PyPI publishing on releases (trusted publishing)
    - **MODERN ACTIONS**: Latest versions (setup-python@v5, upload-artifact@v4, etc.)

- **ACHIEVED**: Repository professionalization and management

  - **MADE PUBLIC**: Successfully converted private repository to public
  - **ENABLED**: GitHub Pages with workflow-based deployment
  - **ADDED**: Professional README badges (CI/CD status, docs, Python version, license)
  - **ADDED**: CODEOWNERS file for repository management and review assignments
  - **ADDED**: Pull request template for consistent contribution workflow
  - **RESOLVED**: All dependency conflicts and CI environment compatibility issues

- **FIXED**: Critical CI/CD dependency and configuration issues

  - **RESOLVED**: `pytest-anyio` version constraint compatibility (>=0.0.0 for CI)
  - **FIXED**: MkDocs navigation references to non-existent files (strict mode)
  - **CORRECTED**: GitHub Actions dependency installation (`--extra dev` syntax)
  - **UPDATED**: All GitHub Actions to latest stable versions
  - **RESULT**: Documentation deployment working perfectly, CI/CD infrastructure complete

### 🎆 Code Quality

- **FIXED**: Code complexity issues in main.py
  - **REFACTORED**: `_validate_symlink_path()` function to reduce cyclomatic complexity from C to acceptable levels
    - **EXTRACTED**: `_validate_symlink_path_exists()` for empty path validation
    - **EXTRACTED**: `_expand_symlink_path()` for path expansion and absolutization
    - **EXTRACTED**: `_validate_symlink_path_characters()` for invalid character checking
    - **EXTRACTED**: `_normalize_and_validate_symlink_path()` for path normalization and validation
  - **REFACTORED**: `_save_updated_configuration()` function to reduce cyclomatic complexity from C to acceptable levels
    - **EXTRACTED**: `_convert_app_to_dict()` for application object to dictionary conversion
    - **EXTRACTED**: `_determine_save_target()` for configuration save location determination
  - **RESULT**: All functions now meet project complexity standards (≤10 cyclomatic complexity)
  - **VERIFIED**: All 95 tests continue to pass after refactoring

### DOCS Documentation

- **ENHANCED**: Documentation navigation with multiple ways to return home

  - **ADDED**: Clickable site title and logo that return to home page
  - **ADDED**: Home icon (`🏠`) to navigation breadcrumbs and home links
  - **ADDED**: Custom CSS styling to enhance home navigation visibility
  - **ADDED**: JavaScript functionality to make header elements clickable
  - **ADDED**: Keyboard shortcut (Alt+H) to quickly return to home page
  - **ADDED**: Enhanced "back to top" button styling and hover effects
  - **ADDED**: Home breadcrumb navigation to key pages (Getting Started, Commands Reference)
  - **ENABLED**: Additional Material theme features including `navigation.prune` and `header.autohide`
  - **RESULT**: Users can now easily navigate back to home from any documentation page
  - **FILES**: `docs/stylesheets/extra.css`, `docs/javascripts/extra.js`, updated `mkdocs.yml`

- **IMPROVED**: Documentation build tasks

  - **ENHANCED**: `docs:build` task with clear progress messages and success feedback
  - **ADDED**: `docs:serve` task for local development server with startup messages
  - **MAINTAINED**: `docs` task as alias for `docs:serve` for backward compatibility
  - **UPDATED**: Clean task now removes `site/` directory for documentation builds

- **FIXED**: Missing MkDocs plugin installation issue

  - **INSTALLED**: `mkdocs-git-revision-date-localized-plugin==1.4.7` with dependency `pytz==2025.2`
  - **RESOLVED**: "The 'git-revision-date-localized' plugin is not installed" error
  - **RESULT**: Documentation now builds successfully with `task docs:build`

### BUG Bug Fixes

- **FIXED**: Edit command exception traceback display issue

  - **PROBLEM**: Setting `--rotation` without symlink showed full exception traceback, creating messy error output
  - **SOLUTION**: Added specific `ValueError` exception handling to display clean error messages without tracebacks
  - **RESULT**: User-friendly error messages like "Error editing application: File rotation requires a symlink path. Use --symlink-path to specify one."
  - **IMPACT**: Cleaner, more professional error output that doesn't overwhelm users with technical details

- **FIXED**: Symlink path validation in edit command

  - **PROBLEM**: `--symlink-path` accepted invalid paths without validation (empty strings, wrong extensions, malformed paths)
  - **SOLUTION**: Added comprehensive symlink path validation with new `_validate_symlink_path()` function
  - **VALIDATES**: Empty/whitespace paths, path structure, invalid characters, parent directory existence
  - **ENFORCES**: `.AppImage` extension requirement for symlink paths
  - **NORMALIZES**: Path expansion (`~` → home directory) and resolution (`..` segments)
  - **EXAMPLES**:
    - Rejects empty paths: `"Symlink path cannot be empty. Provide a valid file path."`
    - Rejects invalid extensions: `"Symlink path should end with '.AppImage': /tmp/invalid"`
    - Properly expands: `~/bin/test.AppImage` → `/home/user/bin/test.AppImage`
  - **IMPACT**: Prevents configuration errors and ensures valid symlink paths for file rotation

### TEST Testing & Quality Assurance

- **NEW**: `test:regression` task in Taskfile.yml for automated regression validation

  - **ADDED**: `task test:regression` command for running regression tests specifically
  - **FOCUSED**: Targets `tests/test_add_regression.py` with verbose output and colored results
  - **INTEGRATED**: Part of comprehensive test suite alongside e2e, smoke, and pattern-matching tests
  - **FEEDBACK**: Provides clear success message when regression tests pass
  - **USAGE**: `task test:regression` - Run regression tests to validate fixed issues remain resolved
  - **AVAILABLE**: Shows up in `task --list` with other test tasks for easy discovery

- **NEW**: Comprehensive Regression Testing for `add` Command

  - **ADDED**: `tests/test_add_regression.py` - Dynamic regression validation using real user configurations
  - **DISCOVERS**: Existing configurations in `~/.config/appimage-updater/apps/` automatically
  - **RECREATES**: Each configuration using enhanced `add` command with extracted parameters
  - **VALIDATES**: Generated configs match originals with intelligent pattern improvements allowed
  - **SUCCESS RATE**: 100% (5/5 existing applications successfully recreated)
  - **REAL-WORLD**: Tests against actual user configurations, not synthetic test data
  - **PROVES**: Complete feature parity - `add` can now handle any existing configuration
  - **EXAMPLES**: Successfully recreates complex configs like:
    - FreeCAD_weekly: prerelease + weekly frequency + rotation + symlink
    - OrcaSlicer_nightly: prerelease + rotation + no checksums
    - FreeCAD: weekly frequency + no rotation + standard checksums
  - **AUTOMATED**: Runs as part of test suite to prevent future regressions

- **ENHANCED**: Comprehensive test coverage for edit command validation fixes

  - Added 7 new tests in `tests/test_edit_validation_fixes.py` covering all validation scenarios
  - Tests no traceback display for validation errors
  - Tests empty, whitespace-only, and invalid extension symlink path validation
  - Tests path expansion (`~` and `..` resolution) and normalization functionality
  - Tests valid symlink paths work correctly with rotation
  - All tests pass with proper text normalization to handle Rich console formatting
  - **RESULT**: Total test coverage increased, all existing tests continue to pass

### 🏧 Architecture & Design

- **ENHANCED**: Perfect Command Symmetry - `add` and `edit` Feature Parity

  - **ACHIEVED**: Complete parameter alignment between `add` and `edit` commands
  - **UPDATED**: `_generate_default_config()` function to accept all new configuration parameters
  - **IMPROVED**: Parameter validation and error handling consistency across commands
  - **STANDARDIZED**: Configuration field handling (always include `rotation_enabled` for consistency)
  - **UNIFIED**: Help text and documentation patterns between commands
  - **BENEFITS**:
    - Users learn one parameter set that works for both commands
    - Reduces cognitive load and documentation complexity
    - Enables complex workflows with single commands
    - Future parameter additions automatically benefit both commands

- **ENHANCED**: Configuration Generation Logic

  - **IMPROVED**: `_generate_default_config()` with comprehensive parameter support:
    - `prerelease`: Boolean control for prerelease versions
    - `unit`: Frequency time unit (hours/days/weeks)
    - `checksum`: Full checksum configuration (enabled, algorithm, pattern, required)
    - `rotation`: Complete file rotation setup (enabled, retain count, symlink path)
  - **CONSISTENT**: Field naming and structure matches existing configurations exactly
  - **VALIDATED**: All parameters undergo proper validation and normalization
  - **DEFAULTS**: Intelligent defaults that match user expectations and current behavior

### VERSION Code Quality & Refactoring

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

### BUG Code Quality Fixes

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

### 🆕 Command Enhancements

- **MAJOR**: Comprehensive `add` Command Enhancement - Feature Parity with `edit`

  - **COMPLETE**: `add` command now supports ALL configuration options available in `edit` command
  - **ELIMINATES**: Need for post-creation edits - create complete configurations in a single command
  - **NEW OPTIONS**: Added all missing parameters for complete control:

  **Basic Configuration:**

  - `--prerelease/--no-prerelease`: Enable/disable prerelease versions (default: disabled)
  - `--unit UNIT`: Frequency units - hours, days, weeks (default: days)
  - `--frequency N --unit UNIT`: Complete frequency specification

  **File Rotation Options:**

  - `--rotation/--no-rotation`: Enable/disable file rotation (default: disabled)
  - `--retain N`: Number of old files to retain (1-10, default: 3)
  - `--symlink PATH`: Managed symlink path (auto-enables rotation)

  **Checksum Verification Options:**

  - `--checksum/--no-checksum`: Enable/disable verification (default: enabled)
  - `--checksum-algorithm ALG`: Algorithm - sha256, sha1, md5 (default: sha256)
  - `--checksum-pattern PATTERN`: Checksum file pattern (default: {filename}-SHA256.txt)
  - `--checksum-required/--checksum-optional`: Make verification required/optional (default: optional)

  **EXAMPLES**: Complete single-command configurations now possible:

  ```bash
  # Prerelease with weekly updates and rotation
  appimage-updater add --prerelease --frequency 1 --unit weeks --rotation \
    --symlink ~/bin/freecad-weekly.AppImage FreeCAD_weekly \
    https://github.com/FreeCAD/FreeCAD ~/Apps/FreeCAD

  # Required checksums with custom settings
  appimage-updater add --checksum-required --checksum-algorithm sha1 \
    --frequency 7 --unit days SecureApp \
    https://github.com/user/secureapp ~/Apps/SecureApp
  ```

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

### 🆕 Show Command Features

- **NEW**: `show` command for detailed application information

  - **ADDED**: `appimage-updater show --app <name>` command to display comprehensive app details
  - **DISPLAYS**: Configuration settings (source, URL, download directory, patterns, frequency, checksum settings)
  - **SHOWS**: File information (size, modification time, executable status) for matching AppImage files
  - **DETECTS**: Symlinks pointing to AppImage files with status validation
  - **SUPPORTS**: Same configuration options as other commands (`--config-dir`)
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

### TEST Show Command Testing

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

### VERSION Configuration Updates

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

### TOOLS Development & Testing

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

______________________________________________________________________

## [Previous] - 2025-01-04

### BUILD Code Quality

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

### LOCK Security

- **NEW**: Automatic checksum verification for downloaded files
  - Supports SHA256, SHA1, and MD5 algorithms
  - Configurable checksum file patterns (e.g., `{filename}-SHA256.txt`)
  - Intelligent detection of checksum files in GitHub releases
  - Visual indicators for verification status in download results
  - Optional or required verification modes per application

### DEPLOY Improvements

- **FIXED**: HTTP redirect handling for GitHub release downloads

  - Downloads now properly follow 302 redirects from GitHub CDN
  - Resolves previous "Redirect response '302 Found'" errors

- **ENHANCED**: Download robustness and reliability

  - Automatic retry logic with exponential backoff (up to 3 attempts)
  - Improved timeout configuration (separate connect/read/write timeouts)
  - Better error handling for network interruptions
  - Progress tracking with transfer speed and ETA

### COMMIT Configuration

- **NEW**: `list` command for viewing configured applications

  - **ADDED**: `appimage-updater list` command to display all configured applications
  - **DISPLAYS**: Application name, enabled/disabled status, source repository, download directory, and update frequency
  - **SUPPORTS**: Same configuration options as other commands (`--config-dir`)
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

### TOOLS Developer Experience

- Enhanced logging with checksum verification status
- Comprehensive debug information for download failures
- Better error messages and user feedback
- Updated documentation with security recommendations

### LIST Technical Details

- Checksum files automatically downloaded and verified
- Support for multiple checksum file formats:
  - Hash + filename: `abc123... filename.AppImage`
  - Hash only: `abc123...`
  - Multiple files: One hash per line
- Configurable patterns support various naming conventions:
  - `{filename}-SHA256.txt` (FreeCAD style)
  - `{filename}_SHA256.txt` (underscore variant)
  - `{filename}.sha256` (extension-based)

### TEST Tested With

- PASS FreeCAD weekly builds (SHA256 verification)
- PASS Large file downloads (>800MB) with retry logic
- PASS GitHub release redirect handling
- PASS Checksum pattern detection and parsing

______________________________________________________________________

## Contributing

This project follows [Semantic Versioning](https://semver.org/).
