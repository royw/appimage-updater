# Architecture

This document describes the architecture and design principles of AppImage Updater.

## High-Level Architecture

```mermaid
graph TB
    A[CLI Interface] --> B[Command Layer]
    B --> C[Configuration Manager]
    B --> D[Repository Factory]
    B --> E[Version Checker]
    B --> F[Downloader]
    B --> G[Distribution Selector]
    B --> H[System Info]
    
    C --> I[JSON Config Files]
    D --> J[GitHub Repository]
    D --> K[GitLab Repository]
    D --> L[Other Repositories]
    J --> M[GitHub Client]
    J --> N[GitHub Auth]
    M --> O[GitHub API]
    E --> P[Version Comparison]
    F --> Q[Concurrent Downloads]
    F --> R[ZIP Extraction]
    F --> S[Checksum Verification]
    F --> T[File Rotation]
    G --> U[Platform Detection]
    H --> V[Architecture Detection]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#ffeb3b
    style E fill:#e8f5e8
    style F fill:#e8f5e8
    style G fill:#fff3e0
    style H fill:#fff3e0
    style J fill:#4caf50
    style K fill:#4caf50
    style L fill:#4caf50
```

## Core Components

### CLI Interface (`main.py`)

The entry point for all user interactions, built with [Typer](https://typer.tiangolo.com/).

**Responsibilities:**

- Parse command-line arguments and options
- Coordinate between different components
- Handle global error handling and logging
- Orchestrate CLI command execution

**Key Features:**

- Rich console output with colors and progress bars
- Async command execution
- Structured error handling with clean user messages
- **Modular architecture** with extracted functionality:
  - `display.py` - Console output formatting and display functions
  - `pattern_generator.py` - GitHub URL parsing and intelligent pattern generation
  - `config_operations.py` - Configuration management and persistence operations
  - `distribution_selector.py` - Intelligent asset selection for multi-platform releases
  - `system_info.py` - System detection for compatibility filtering
  - `github_auth.py` - GitHub authentication management

#### Supporting Modules

**Display Module (`display.py`)**

- Console output formatting and styling
- Table generation and data presentation
- Progress indicators and status messages
- Rich console integration for enhanced UX
- Application listing and details display
- Check and download results formatting

**Pattern Generation (`pattern_generator.py`)**

- GitHub repository URL parsing and validation
- Intelligent AppImage pattern generation from actual releases
- Async GitHub API integration for pattern discovery
- Fallback pattern generation strategies
- Source type detection and URL normalization

**Configuration Operations (`config_operations.py`)**

- Application configuration loading and saving
- Configuration file and directory management
- Application addition, removal, and editing operations
- Configuration validation and error handling
- Default configuration generation
- Directory creation and validation

**Distribution Selector (`distribution_selector.py`)**

- Distribution-aware asset selection for multi-platform releases
- Automatic compatibility detection based on system information
- Interactive selection when automatic detection isn't possible
- Support for Ubuntu, Fedora, Arch, openSUSE, and other distributions
- Version compatibility scoring and selection

**System Information (`system_info.py`)**

- Comprehensive system detection (architecture, platform, distribution)
- Architecture compatibility checking (x86_64, arm64, i686, etc.)
- Platform detection (Linux, macOS, Windows)
- Supported format detection (.AppImage, .deb, .rpm, etc.)
- Distribution family identification for compatibility

**GitHub Authentication (`github_auth.py`)**

- GitHub token discovery from multiple sources
- Environment variable and config file token support
- GitHub CLI integration for token discovery
- Security-first priority ordering for token sources
- Authentication validation and error handling

### Configuration System

#### Configuration Models (`config.py`)

Pydantic-based models providing type-safe configuration validation.

**Models:**

- `GlobalConfig` - Global settings (timeouts, concurrency, logging)
- `ChecksumConfig` - Checksum verification settings
- `FrequencyConfig` - Update frequency configuration
- `ApplicationConfig` - Per-application settings

#### Configuration Loader (`config_loader.py`)

Handles loading and validation of configuration files.

**Features:**

- Single file and directory-based configuration
- Hierarchical configuration merging
- Path expansion and validation
- Error reporting with context

### Data Models (`models.py`)

Core data structures used throughout the application.

**Key Models:**

- `Release` - GitHub release information
- `Asset` - Download asset with checksum association
- `UpdateCandidate` - Available update with metadata
- `CheckResult` - Update check results
- `DownloadResult` - Download operation results
- `ChecksumResult` - Checksum verification results

### Repository Abstraction Layer (`repositories/`)

Extensible abstraction layer supporting multiple repository platforms with a unified interface.

**Architecture:**

- **Abstract Base Class** (`base.py`) - Common interface for all repository types
- **Factory Pattern** (`factory.py`) - Automatic client instantiation based on URL detection
- **GitHub Implementation** (`github_repository.py`) - Wrapper around existing GitHub client
- **Example Implementation** (`example_gitlab_repository.py`) - Template for adding new platforms

**Key Components:**

#### Repository Client Interface (`repositories/base.py`)

Abstract base class defining the common interface for all repository clients:

```python
class RepositoryClient(ABC):
    @abstractmethod
    async def get_latest_release(self, url: str) -> Release:
        """Get the latest release from repository."""
    
    @abstractmethod
    async def get_releases(self, url: str, limit: int = 10) -> list[Release]:
        """Get recent releases from repository."""
    
    @abstractmethod
    def parse_repo_url(self, url: str) -> tuple[str, str]:
        """Parse repository URL to extract owner and repo name."""
    
    @abstractmethod
    def normalize_repo_url(self, url: str) -> tuple[str, bool]:
        """Normalize repository URL and detect corrections."""
```

#### Repository Factory (`repositories/factory.py`)

Factory pattern implementation for automatic client creation:

```python
def get_repository_client(url: str, **kwargs) -> RepositoryClient:
    """Create appropriate repository client based on URL pattern."""
    
def detect_repository_type(url: str) -> str:
    """Detect repository type from URL (github, gitlab, etc.)."""
```

**Features:**

- **URL-based Detection** - Automatically selects appropriate client
- **Extensible Design** - Easy addition of new repository types
- **Error Handling** - Graceful fallback and error reporting
- **Configuration Support** - Repository-specific options

#### GitHub Repository Implementation (`repositories/github_repository.py`)

Wrapper around the existing GitHub client maintaining full compatibility:

**Features:**

- Rate limiting awareness and respect
- Automatic checksum file detection and association
- Asset filtering and pattern matching
- Error handling with exponential backoff retries
- Authentication integration with `github_auth.py`
- Release caching and efficient API usage

**Key Methods:**

- `get_releases()` - Fetch repository releases (latest or all)
- `find_checksum_assets()` - Locate and parse checksum files
- `associate_assets_with_checksums()` - Link download assets to checksums
- `filter_assets_by_pattern()` - Pattern-based asset filtering
- `get_release_by_tag()` - Fetch specific release by tag

### Legacy GitHub Integration (`github_client.py`)

Direct GitHub API client used internally by the GitHub repository implementation.

**Note:** This module is now wrapped by `GitHubRepository` and accessed through the repository abstraction layer.

### Version Management (`version_checker.py`)

Handles version detection and comparison logic with intelligent fallback strategies.

**Components:**

- **Version Metadata System**: Reads version from `.info` metadata files for accurate tracking
- **Fallback Version Extraction**: Regex-based filename parsing when metadata unavailable
- **Semantic Version Parsing**: Uses `packaging.version` for proper version comparison
- **Multi-Format Support**: Works with `.zip`, `.AppImage`, and other release formats
- **Current Version Detection**: Scans local files with pattern matching

**Version Metadata Features:**

```bash
# Automatically created during downloads
Bambu_Studio_ubuntu-24.04_PR-8017.zip      # Downloaded file
Bambu_Studio_ubuntu-24.04_PR-8017.zip.info # Metadata: "Version: v02.02.01.60"
```

**Benefits:**

- Avoids incorrect parsing of OS versions ("ubuntu-24.04") as app versions
- Uses actual GitHub release tags for accurate version tracking
- Supports complex filename patterns and multi-format releases
- Automatically rotates metadata files alongside main files

### Download Engine (`downloader.py`)

Concurrent download manager with comprehensive features.

**Capabilities:**

- Concurrent downloads with semaphore limiting
- Progress tracking with rich progress bars
- Automatic retry with exponential backoff
- **Automatic ZIP extraction** - Extracts AppImages from ZIP archives
- **Version metadata file creation** (`.info` files with release tags)
- Checksum verification (SHA256, SHA1, MD5)
- File rotation with configurable retention (includes metadata files)
- Symlink management

**ZIP Extraction Features:**

- Automatic detection of ZIP files by extension
- Scans ZIP contents for `.AppImage` files
- Extracts AppImages from subdirectories within ZIP files
- Removes original ZIP file after successful extraction
- Handles multiple AppImages (uses first found, logs warning)
- Comprehensive error handling for invalid ZIP files
- Seamless integration with rotation and checksum systems

### Logging (`logging_config.py`)

Centralized logging configuration using [Loguru](https://loguru.readthedocs.io/).

**Features:**

- Console and file logging with different levels
- Structured log formatting
- Automatic log rotation (10MB files, 7-day retention)
- Debug mode with verbose output

## Design Principles

### Async-First Architecture

All I/O operations use `asyncio` for better performance and responsiveness.

```python
async def check_updates(apps: list[ApplicationConfig]) -> list[CheckResult]:
    """Check for updates across multiple applications concurrently."""
    tasks = [check_single_app(app) for app in apps]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

### Type Safety

Comprehensive type annotations with strict mypy checking.

```python
def parse_version(filename: str, patterns: list[str]) -> tuple[str | None, str]:
    """Parse version from filename using regex patterns.
    
    Returns:
        Tuple of (version, original_filename)
    """
```

### Error Handling

Structured exception hierarchy with user-friendly messages.

```python
class AppImageUpdaterError(Exception):
    """Base exception for all application errors."""

class ConfigurationError(AppImageUpdaterError):
    """Configuration validation and loading errors."""

class NetworkError(AppImageUpdaterError):
    """Network-related errors (GitHub API, downloads)."""
```

### Configuration-Driven

Flexible JSON configuration supporting multiple deployment patterns.

```json
{
  "global_config": {
    "concurrent_downloads": 3,
    "timeout": 30
  },
  "applications": [...]
}
```

## Data Flow

### Application Addition Flow

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as CLI
    participant C as Config
    participant V as Validator
    
    U->>CLI: add FreeCAD github.com/FreeCAD/FreeCAD ~/Apps
    CLI->>V: Validate URL and path
    V-->>CLI: Validation results
    CLI->>C: Generate config with defaults
    C->>C: Smart pattern generation
    C->>C: Create directory if needed
    CLI-->>U: Success with generated config
```

### Update Check Flow

```mermaid
sequenceDiagram
    participant CLI as CLI
    participant GH as GitHub Client
    participant VC as Version Checker
    participant D as Downloader
    
    CLI->>GH: Get latest releases
    GH-->>CLI: Release data with assets
    CLI->>VC: Compare with local versions
    VC-->>CLI: Update candidates
    CLI->>D: Download if updates available
    D->>D: Verify checksums
    D->>D: Rotate files if configured
    D-->>CLI: Download results
```

### Configuration Loading

```mermaid
graph TD
    A[Config Path] --> B{Single File?}
    B -->|Yes| C[Load config.json]
    B -->|No| D[Scan directory]
    D --> E[Load global.json]
    D --> F[Load app configs]
    C --> G[Validate Schema]
    E --> G
    F --> G
    G --> H[Merge Configurations]
    H --> I[Create Application Objects]
```

## Security Considerations

### Checksum Verification

All downloads support checksum verification:

- **SHA256** (recommended) - Cryptographically secure
- **SHA1** - Legacy support
- **MD5** - Legacy support (not recommended)

### Path Validation

- Path traversal prevention
- Symlink validation
- Directory creation safety
- File permission handling

### Network Security

- HTTPS-only connections
- Request timeout enforcement
- User-agent identification
- Error message sanitization

## Performance Optimizations

### Concurrent Operations

- Parallel update checks across applications
- Concurrent downloads with rate limiting
- Async I/O for all network operations

### Caching Strategy

- GitHub API response caching (planned)
- Local version detection caching
- Pattern compilation caching

### Memory Management

- Streaming downloads for large files
- Progressive loading of configuration
- Efficient regex pattern reuse

## Testing Architecture

### Test Organization

```text
tests/
├── test_e2e.py              # End-to-end integration tests
├── test_edit_command.py     # CLI command testing
├── test_edit_validation_fixes.py  # Validation testing
└── test_rotation.py         # File rotation testing
```

### Testing Strategies

- **Unit Tests** - Individual component testing
- **Integration Tests** - Component interaction testing
- **End-to-End Tests** - Complete workflow testing
- **Property-Based Tests** - Input validation testing

### Mock Strategies

- GitHub API response mocking
- File system operation mocking
- Network request mocking
- Time-based operation mocking

## Repository Factory Pattern

The repository abstraction layer uses the factory pattern to automatically select and instantiate the appropriate repository client based on URL analysis.

### Factory Implementation

```python
def get_repository_client(url: str, **kwargs) -> RepositoryClient:
    """Create appropriate repository client based on URL detection."""
    repository_types = [
        GitHubRepository,
        # Future repository types added here
    ]
    
    for repo_class in repository_types:
        temp_client = repo_class(**kwargs)
        if temp_client.detect_repository_type(url):
            return temp_client
    
    raise RepositoryError(f"No repository client available for URL: {url}")
```

### URL Detection Strategy

Each repository implementation provides URL detection logic:

- **GitHub**: Detects `github.com` and `www.github.com` domains
- **GitLab**: Would detect `gitlab.com` and self-hosted GitLab instances
- **Bitbucket**: Would detect `bitbucket.org` domains

### Benefits

- **Automatic Selection** - No manual client specification required
- **Extensible** - New repository types integrate seamlessly
- **Backward Compatible** - Existing configurations work unchanged
- **Error Handling** - Clear error messages for unsupported URLs

### Direct Download Repository Handlers

The system now supports applications that don't use traditional repository APIs through specialized handlers:

#### DirectDownloadRepository

Handles applications with static download URLs or "latest" symlinks:

- **Use Cases**: YubiKey Manager, OpenRGB with direct AppImage links
- **Detection Patterns**:
  - URLs ending with `-latest*.AppImage`
  - Direct `.AppImage` file URLs
  - Generic `/download/` endpoints
- **Version Detection**: Extracts versions from URLs using regex patterns
- **Limitations**: No historical release information, single release per check

#### DynamicDownloadRepository

Handles applications with JavaScript-generated or dynamic download pages:

- **Use Cases**: Applications with dynamic download generation
- **Detection Patterns**:
  - Dynamic download page URLs
  - Generic download pages requiring content parsing
- **Content Parsing**: Scrapes HTML for AppImage download links
- **Version Extraction**: Attempts to find version information in page content or URLs

#### Repository Handler Selection

The factory uses a priority-based selection system:

1. **GitHubRepository** - Highest priority for GitHub URLs
1. **DynamicDownloadRepository** - Checks for dynamic patterns first
1. **DirectDownloadRepository** - Fallback for direct download patterns

This ordering ensures more specific handlers are tried before generic ones.

## Extensibility

### Adding New Repository Types

The repository abstraction layer makes adding new platforms straightforward:

1. **Create Repository Implementation**

   ```python
   class GitLabRepository(RepositoryClient):
       def detect_repository_type(self, url: str) -> bool:
           return "gitlab.com" in url.lower()
       
       async def get_releases(self, url: str, limit: int = 10) -> list[Release]:
           # GitLab API implementation
   ```

1. **Register in Factory**

   ```python
   # Add to repository_types list in factory.py
   repository_types = [
       GitHubRepository,
       DynamicDownloadRepository,  # Check dynamic before direct (more specific)
       DirectDownloadRepository,
       GitLabRepository,  # New addition
   ]
   ```

1. **Add Configuration Support**

   - Update URL validation patterns
   - Add repository-specific configuration options
   - Update documentation and examples

1. **Implement Tests**

   - Unit tests for repository implementation
   - Integration tests with factory
   - End-to-end tests with real URLs

### Plugin Architecture (Planned)

Future plugin system for:

- Custom source types
- Custom download handlers
- Custom notification systems
- Custom validation rules

## Deployment Considerations

### Distribution

- PyPI package distribution
- Single executable via PyInstaller
- Docker container support
- System package formats (deb, rpm)

### Configuration Management

- XDG Base Directory Specification compliance
- Environment variable overrides
- Configuration validation and migration
- Backup and restore utilities

## Monitoring and Observability

### Logging Levels

- **DEBUG** - Detailed operation tracing
- **INFO** - General operational information
- **WARNING** - Non-critical issues
- **ERROR** - Operation failures

### Metrics Collection (Planned)

- Update check frequency
- Download success rates
- Application popularity
- Error categorization

This architecture provides a robust, maintainable, and extensible foundation for AppImage management automation.
