# GitLab Repository Support Implementation Plan

## Overview

This document outlines the comprehensive plan for adding GitLab repository support to AppImage Updater. The implementation leverages the existing repository abstraction architecture to provide seamless GitLab integration alongside GitHub support.

## GitLab API Analysis

### Key Findings

**GitLab API Structure:**

- **Endpoint**: `GET /projects/:id/releases` (uses project IDs instead of owner/repo)
- **Latest Release**: `GET /projects/:id/releases/permalink/latest`
- **Assets Structure**: Two types - `sources` (auto-generated archives) and `links` (custom release assets)
- **Authentication**: Personal Access Tokens via `PRIVATE-TOKEN` header
- **Project Identification**: Supports both numeric project IDs and URL-encoded paths

**Key Differences from GitHub:**

1. **Project ID System**: GitLab uses project IDs instead of owner/repo pairs
1. **Dual Asset Types**: Auto-generated source archives + custom linked assets
1. **Self-Hosted Support**: Must handle both gitlab.com and custom GitLab instances
1. **URL Structure**: `https://gitlab.com/owner/project` vs GitHub's format

### GitLab Release Response Structure

```json
{
    "tag_name": "v0.2",
    "name": "Awesome app v0.2 beta", 
    "description": "Release notes...",
    "created_at": "2019-01-03T01:56:19.539Z",
    "released_at": "2019-01-03T01:56:19.539Z",
    "assets": {
        "count": 6,
        "sources": [
            {
                "format": "zip",
                "url": "https://gitlab.example.com/root/awesome-app/-/archive/v0.2/awesome-app-v0.2.zip"
            }
        ],
        "links": [
            {
                "id": 2,
                "name": "awesome-v0.2.msi",
                "url": "http://192.168.10.15:3000/msi",
                "link_type": "other"
            }
        ]
    }
}
```

## Implementation Strategy

### Phase 1: Core GitLab Infrastructure (High Priority)

#### 1.1 GitLab Authentication Module

**File**: `src/appimage_updater/gitlab/auth.py`

```python
class GitLabAuth:
    """GitLab authentication using personal access tokens."""
    
    def __init__(self, token: str | None = None):
        # Support GITLAB_TOKEN environment variable
        # Handle token validation and headers
    
    def get_headers(self) -> dict[str, str]:
        # Return PRIVATE-TOKEN header for API requests
        
    def is_authenticated(self) -> bool:
        # Check if valid token is available
```

**Features:**

- Personal Access Token support
- Environment variable integration (`GITLAB_TOKEN`)
- Header generation for API requests
- Token validation

#### 1.2 GitLab API Client

**File**: `src/appimage_updater/gitlab/client.py`

```python
class GitLabClient:
    """GitLab API v4 client for release information."""
    
    def __init__(self, timeout: int = 30, user_agent: str | None = None, auth: GitLabAuth | None = None):
        # Initialize HTTP client with GitLab-specific configuration
        
    async def get_project_id(self, owner: str, repo: str, base_url: str = "https://gitlab.com") -> str:
        # Convert owner/repo to GitLab project ID or URL-encoded path
        
    async def get_latest_release(self, project_id: str, base_url: str = "https://gitlab.com") -> dict[str, Any]:
        # GET /projects/:id/releases/permalink/latest
        
    async def get_releases(self, project_id: str, base_url: str = "https://gitlab.com", limit: int = 10) -> list[dict[str, Any]]:
        # GET /projects/:id/releases with pagination
        
    async def should_enable_prerelease(self, project_id: str, base_url: str = "https://gitlab.com") -> bool:
        # Check if only prereleases exist
```

**Features:**

- Async HTTP client using httpx
- Project ID resolution from owner/repo
- Release fetching with pagination
- Prerelease detection
- Self-hosted GitLab support

#### 1.3 GitLab Repository Implementation

**File**: `src/appimage_updater/gitlab/repository.py`

```python
class GitLabRepository(RepositoryClient):
    """GitLab repository implementation following the abstract base."""
    
    def __init__(self, timeout: int = 30, user_agent: str | None = None, auth: GitLabAuth | None = None, token: str | None = None, **kwargs: Any):
        # Initialize with GitLab-specific parameters
    
    @property
    def repository_type(self) -> str:
        return "gitlab"
    
    def detect_repository_type(self, url: str) -> bool:
        # Detect gitlab.com and self-hosted GitLab instances
        
    def parse_repo_url(self, url: str) -> tuple[str, str]:
        # Extract owner/repo from GitLab URLs
        
    def normalize_repo_url(self, url: str) -> tuple[str, bool]:
        # Normalize GitLab URLs and detect corrections
        
    async def get_latest_release(self, repo_url: str) -> Release:
        # Map GitLab release data to AppImage Updater Release model
        
    async def get_releases(self, repo_url: str, limit: int = 10) -> list[Release]:
        # Fetch and convert multiple releases
        
    async def should_enable_prerelease(self, url: str) -> bool:
        # Check prerelease status for repository
        
    async def generate_pattern_from_releases(self, url: str) -> str | None:
        # Generate file patterns from GitLab releases
```

**Features:**

- Full RepositoryClient interface implementation
- GitLab URL detection and parsing
- Asset mapping from GitLab format to Release model
- Pattern generation from actual releases
- Error handling with GitLab-specific exceptions

### Phase 2: Asset Handling & URL Detection (Medium Priority)

#### 2.1 GitLab Asset Mapping

```python
def _map_gitlab_assets_to_release(gitlab_release: dict[str, Any]) -> Release:
    """Convert GitLab release format to AppImage Updater Release model."""
    # Priority order:
    # 1. Custom links with AppImage files
    # 2. Custom links with other binaries
    # 3. Auto-generated source archives
    
    assets = []
    
    # Process custom linked assets first (higher priority)
    for link in gitlab_release.get("assets", {}).get("links", []):
        if link["name"].lower().endswith(".appimage"):
            # Prioritize AppImage files
            assets.insert(0, create_asset_from_link(link))
        else:
            assets.append(create_asset_from_link(link))
    
    # Add source archives as fallback
    for source in gitlab_release.get("assets", {}).get("sources", []):
        assets.append(create_asset_from_source(source))
    
    return Release(
        tag_name=gitlab_release["tag_name"],
        name=gitlab_release["name"],
        assets=assets,
        # ... other fields
    )
```

#### 2.2 URL Detection & Normalization

```python
def _detect_gitlab_url(url: str) -> bool:
    """Detect GitLab URLs including self-hosted instances."""
    # gitlab.com patterns
    if "gitlab.com" in url:
        return True
    
    # Self-hosted GitLab detection
    # Look for GitLab-specific API endpoints or UI patterns
    try:
        # Probe for GitLab API endpoint
        api_url = f"{base_url}/api/v4/version"
        # Make HEAD request to check if it's GitLab
        return check_gitlab_api_endpoint(api_url)
    except Exception:
        return False

def _normalize_gitlab_url(url: str) -> tuple[str, bool]:
    """Normalize GitLab URLs and detect corrections."""
    original_url = url
    
    # Remove .git suffix
    if url.endswith(".git"):
        url = url[:-4]
    
    # Remove trailing slashes
    url = url.rstrip("/")
    
    # Ensure proper HTTPS protocol
    if url.startswith("http://"):
        url = url.replace("http://", "https://", 1)
    
    # Convert various GitLab URL formats to canonical form
    # Handle project URLs, release URLs, etc.
    
    was_corrected = url != original_url
    return url, was_corrected
```

### Phase 3: Integration & Factory Updates (Medium Priority)

#### 3.1 Repository Factory Integration

**File**: `src/appimage_updater/repositories/factory.py`

```python
# Add GitLab import
from ..gitlab.repository import GitLabRepository

def get_repository_client(...):
    # Update type mapping
    type_mapping = {
        "github": GitHubRepository,
        "gitlab": GitLabRepository,  # Add GitLab support
        "direct_download": DirectDownloadRepository,
        "dynamic_download": DynamicDownloadRepository,
        "direct": DirectDownloadRepository,
    }
    
    # Update detection order
    repository_types = [
        GitHubRepository,
        GitLabRepository,  # Add GitLab detection
        DynamicDownloadRepository,
        DirectDownloadRepository,
    ]
```

#### 3.2 Configuration Support

```python
# Support explicit GitLab source_type in application configs
{
    "name": "MyGitLabApp",
    "url": "https://gitlab.com/owner/project",
    "source_type": "gitlab",  # Explicit GitLab repository
    "enabled": true,
    "download_dir": "/path/to/downloads",
    # ... other standard configuration options
}

# Self-hosted GitLab example
{
    "name": "SelfHostedApp", 
    "url": "https://git.company.com/team/project",
    "source_type": "gitlab",
    "enabled": true,
    # ... configuration
}
```

### Phase 4: Advanced Features (Low Priority)

#### 4.1 Self-Hosted GitLab Support

**Features:**

- Auto-detect GitLab instances via API endpoint probing
- Support custom base URLs in configuration
- Handle different GitLab versions and API variations
- Configurable API endpoints for enterprise installations

**Implementation:**

```python
class GitLabInstanceDetector:
    """Detect and validate GitLab instances."""
    
    async def detect_gitlab_instance(self, base_url: str) -> bool:
        # Probe /api/v4/version endpoint
        # Check for GitLab-specific headers
        # Validate API compatibility
        
    async def get_api_version(self, base_url: str) -> str:
        # Determine GitLab version for compatibility
```

#### 4.2 Project ID Optimization

**Features:**

- Cache project ID lookups to reduce API calls
- Support direct project ID specification in URLs
- Handle URL-encoded project paths efficiently
- Batch project resolution for multiple repositories

**Implementation:**

```python
class ProjectIdCache:
    """Cache GitLab project ID lookups."""
    
    def __init__(self, ttl: int = 3600):
        # Time-based cache with configurable TTL
        
    async def get_project_id(self, owner: str, repo: str, base_url: str) -> str:
        # Check cache first, then API lookup
        
    def invalidate(self, owner: str, repo: str, base_url: str) -> None:
        # Manual cache invalidation
```

## Technical Considerations

### API Rate Limits

- **GitLab.com**: 2000 requests/hour for authenticated users
- **Self-hosted**: Configurable by administrators
- **Implementation**: Rate limiting and exponential backoff retry logic

### Authentication Options

- **Personal Access Tokens** (recommended for users)
- **GitLab CI/CD Job Tokens** (for CI environments)
- **OAuth2** (future enhancement)
- **Environment Variables**: `GITLAB_TOKEN`, `GITLAB_BASE_URL`

### Asset Priority Logic

1. **Custom Links with AppImage files** (highest priority)
1. **Custom Links with other binaries** (medium priority)
1. **Auto-generated source archives** (fallback)

### Error Handling

- GitLab-specific error response parsing
- Graceful degradation for unsupported GitLab versions
- Clear error messages for authentication failures
- Network timeout and retry handling

## Testing Strategy

### Unit Tests

**Location**: `tests/unit/gitlab/`

```python
# Test files to create:
- test_gitlab_auth.py
- test_gitlab_client.py  
- test_gitlab_repository.py
- test_gitlab_url_detection.py
- test_gitlab_asset_mapping.py
```

**Coverage Areas:**

- Mock GitLab API responses
- URL detection and parsing logic
- Asset mapping and prioritization
- Authentication header generation
- Error handling scenarios

### Integration Tests

**Location**: `tests/integration/gitlab/`

```python
# Test files to create:
- test_gitlab_real_api.py
- test_gitlab_self_hosted.py
- test_gitlab_factory_integration.py
```

**Coverage Areas:**

- Real GitLab API calls (with test repositories)
- Self-hosted GitLab instance testing
- Repository factory integration
- End-to-end configuration workflows

### Regression Tests

**Location**: `tests/regression/`

**Coverage Areas:**

- Ensure GitHub functionality remains intact
- Verify factory detection order works correctly
- Test mixed GitHub/GitLab configurations
- Performance impact assessment

## Implementation Timeline

### Phase 1: Foundation (Week 1-2)

- [ ] GitLab authentication module
- [ ] GitLab API client
- [ ] Basic GitLabRepository implementation
- [ ] Unit tests for core functionality

### Phase 2: Integration (Week 3)

- [ ] Repository factory updates
- [ ] URL detection and normalization
- [ ] Asset mapping logic
- [ ] Integration tests

### Phase 3: Polish (Week 4)

- [ ] Self-hosted GitLab support
- [ ] Performance optimizations
- [ ] Comprehensive error handling
- [ ] Documentation updates

### Phase 4: Validation (Week 5)

- [ ] End-to-end testing
- [ ] Regression test suite
- [ ] Performance benchmarking
- [ ] User acceptance testing

## Configuration Examples

### Basic GitLab Repository

```bash
# Add GitLab repository
appimage-updater add MyGitLabApp https://gitlab.com/owner/project

# Explicit source type
appimage-updater add MyGitLabApp https://gitlab.com/owner/project --source-type gitlab
```

### Self-Hosted GitLab

```bash
# Self-hosted GitLab instance
appimage-updater add CompanyApp https://git.company.com/team/project --source-type gitlab

# With authentication
GITLAB_TOKEN=your_token appimage-updater add CompanyApp https://git.company.com/team/project
```

### Configuration File

```json
{
  "applications": {
    "MyGitLabApp": {
      "name": "MyGitLabApp",
      "url": "https://gitlab.com/owner/project",
      "source_type": "gitlab",
      "enabled": true,
      "download_dir": "/home/user/Applications",
      "pattern": "(?i)MyApp.*\\.AppImage$",
      "prerelease": false
    }
  }
}
```

## Success Criteria

### Functional Requirements

- [ ] GitLab repositories can be added and configured
- [ ] Release detection works for both gitlab.com and self-hosted instances
- [ ] Asset prioritization correctly handles AppImage files
- [ ] Authentication works with personal access tokens
- [ ] All existing GitHub functionality remains intact

### Performance Requirements

- [ ] GitLab API calls complete within reasonable timeouts
- [ ] No significant performance degradation for GitHub repositories
- [ ] Efficient project ID caching reduces redundant API calls

### Quality Requirements

- [ ] 90%+ test coverage for new GitLab modules
- [ ] All existing tests continue to pass
- [ ] No regressions in GitHub repository functionality
- [ ] Clean error messages for GitLab-specific failures

## Future Enhancements

### Additional Repository Types

- **Gitea/Forgejo**: Similar API structure to GitLab
- **Bitbucket**: Different API but similar concepts
- **SourceForge**: Legacy but still used for some projects
- **Codeberg**: Gitea-based public instance

### Advanced Features

- **OAuth2 Authentication**: More secure than personal tokens
- **Webhook Support**: Real-time update notifications
- **Repository Mirroring**: Automatic failover between mirrors
- **Bulk Operations**: Manage multiple repositories efficiently

This plan provides a comprehensive roadmap for implementing GitLab support while maintaining the high quality and architectural standards of the AppImage Updater project.
