# Code Duplication Reduction Plan

**Current Status:** 9.94/10 duplication score (excellent, but can be improved)

**Analysis Date:** 2025-10-01

## Overview

The `task lint:duplication` analysis identified several categories of code duplication that can be refactored to improve maintainability and reduce technical debt.

## Duplication Categories

### 1. Command Validation Pattern (HIGH PRIORITY)

**Locations:**

- `commands/edit_command.py:106-111`
- `commands/remove_command.py:55-62`
- `commands/repository_command.py:86-91`
- `commands/show_command.py:46-53`

**Duplicated Code:**

```python
validation_errors = self.validate()
if validation_errors:
    error_msg = f"Validation errors: {', '.join(validation_errors)}"
    self.console.print(f"[red]Error: {error_msg}[/red]")
    return CommandResult(success=False, message=error_msg, exit_code=1)
```

**Refactoring Strategy:**

- Create a base command class with a `_handle_validation_errors()` method
- All command classes inherit from this base class
- Reduces duplication across 4+ command files

**Implementation:**

```python
# commands/base_command.py
class BaseCommand:
    def _handle_validation_errors(self) -> CommandResult | None:
        """Handle validation errors consistently across commands."""
        validation_errors = self.validate()
        if validation_errors:
            error_msg = f"Validation errors: {', '.join(validation_errors)}"
            self.console.print(f"[red]Error: {error_msg}[/red]")
            return CommandResult(success=False, message=error_msg, exit_code=1)
        return None
```

**Impact:** Reduces 20+ lines of duplicated code

______________________________________________________________________

### 2. Output Formatter Context Pattern (MEDIUM PRIORITY)

**Locations:**

- `commands/add_command.py:65-73`
- `commands/repository_command.py:51-59`
- `cli/handlers/list_handler.py:76-82`
- `cli/handlers/repository_handler.py:110-115`

**Duplicated Code:**

```python
if output_formatter:
    return await self._execute_with_formatter_context(output_formatter)
else:
    return await self._execute_without_formatter()

async def _execute_with_formatter_context(self, output_formatter: Any) -> CommandResult:
    """Execute command with output formatter context."""
    with OutputFormatterContext(output_formatter):
        # command execution
```

**Refactoring Strategy:**

- Create a decorator or mixin for formatter context handling
- Simplify command execution flow
- Standardize formatter usage across all commands

**Implementation:**

```python
# commands/mixins.py
class FormatterContextMixin:
    async def execute_with_optional_formatter(
        self, 
        output_formatter: Any,
        execution_func: Callable
    ) -> CommandResult:
        """Execute command with optional formatter context."""
        if output_formatter:
            with OutputFormatterContext(output_formatter):
                return await execution_func()
        else:
            return await execution_func()
```

**Impact:** Reduces 30+ lines of duplicated code

______________________________________________________________________

### 3. Error Handling Pattern (MEDIUM PRIORITY)

**Locations:**

- `core/repository_operations.py:174-184`
- `core/update_operations.py:303-309`

**Duplicated Code:**

```python
formatter = get_output_formatter()
if formatter:
    formatter.print_error(f"Configuration error: {e}")
else:
    console.print(f"[red]Configuration error: {e}")
# Note: Don't log to stdout as it contaminates JSON output
```

**Refactoring Strategy:**

- Create a centralized error display utility
- Handles formatter availability automatically
- Consistent error messaging across the application

**Implementation:**

```python
# ui/error_display.py
def display_error(message: str, error_type: str = "Error") -> None:
    """Display error message using formatter if available, otherwise console."""
    formatter = get_output_formatter()
    if formatter:
        formatter.print_error(f"{error_type}: {message}")
    else:
        console.print(f"[red]{error_type}: {message}[/red]")
```

**Impact:** Reduces 15+ lines of duplicated code

______________________________________________________________________

### 4. Table Creation Pattern (LOW PRIORITY)

**Locations:**

- `ui/display.py:211-216`
- `ui/output/rich_formatter.py:161-167`

**Duplicated Code:**

```python
table = Table(title="Configured Applications")
table.add_column("Application", style="cyan", no_wrap=False)
table.add_column("Status", style="green")
table.add_column("Source", style="yellow", no_wrap=False, overflow="fold")
table.add_column("Download Directory", style="magenta", no_wrap=False)
```

**Refactoring Strategy:**

- Create a table factory/builder class
- Define table schemas as configuration
- Reuse table definitions across display and formatter modules

**Implementation:**

```python
# ui/table_factory.py
class TableFactory:
    @staticmethod
    def create_applications_table(title: str = "Configured Applications") -> Table:
        """Create standard applications table."""
        table = Table(title=title)
        table.add_column("Application", style="cyan", no_wrap=False)
        table.add_column("Status", style="green")
        table.add_column("Source", style="yellow", no_wrap=False, overflow="fold")
        table.add_column("Download Directory", style="magenta", no_wrap=False)
        return table
```

**Impact:** Reduces 10+ lines of duplicated code

______________________________________________________________________

### 5. Repository URL Handling (LOW PRIORITY)

**Locations:**

- `repositories/direct_download_repository.py` (multiple locations)
- `repositories/dynamic_download_repository.py` (multiple locations)

**Duplicated Patterns:**

- URL normalization: `normalize_repo_url()`
- Version extraction: `_extract_version_from_url()`
- Release fetching: `get_releases()`

**Refactoring Strategy:**

- Create a base repository class with common URL handling
- Extract shared URL parsing utilities
- Reduce duplication between direct and dynamic download repositories

**Implementation:**

```python
# repositories/base_download_repository.py
class BaseDownloadRepository:
    def normalize_repo_url(self, url: str) -> tuple[str, bool]:
        """Normalize download URL (shared implementation)."""
        return url, False
    
    def _extract_version_from_url(self, url: str) -> str:
        """Extract version from URL using common patterns."""
        # Shared implementation
        pass
```

**Impact:** Reduces 50+ lines of duplicated code

______________________________________________________________________

### 6. Command Factory Parameter Passing (LOW PRIORITY)

**Locations:**

- `cli/handlers/check_handler.py:75-80`
- `cli/handlers/remove_handler.py:50-55`
- `cli/handlers/repository_handler.py:56-61`
- `commands/factory.py` (multiple locations)

**Duplicated Code:**

```python
info=info,
instrument_http=instrument_http,
http_stack_depth=http_stack_depth,
http_track_headers=http_track_headers,
trace=trace,
```

**Refactoring Strategy:**

- Create a parameter dataclass for instrumentation settings
- Pass single object instead of multiple parameters
- Reduces parameter list complexity

**Implementation:**

```python
# commands/parameters.py
@dataclass
class InstrumentationParams:
    info: bool = False
    instrument_http: bool = False
    http_stack_depth: int = 3
    http_track_headers: bool = False
    trace: bool = False

# Usage
instrumentation = InstrumentationParams(
    info=info,
    instrument_http=instrument_http,
    # ...
)
command = factory.create_check_command(..., instrumentation=instrumentation)
```

**Impact:** Reduces parameter list complexity, improves readability

______________________________________________________________________

### 7. Version File Handling (LOW PRIORITY)

**Locations:**

- `core/local_version_service.py:127-136`
- `core/version_checker.py:218-227`

**Duplicated Code:**

```python
if version_str:
    version_files.append((version_str, file_path.stat().st_mtime, file_path))
return version_files

def _select_newest_version(self, version_files: list[tuple[str, float, Path]]) -> str:
    """Select the newest version from the list of version files."""
    try:
        # Sort by version (descending) then by modification time (newest first)
        version_files.sort(key=lambda x: (version.parse(x[0].lstrip("v")), x[1]), reverse=True)
```

**Refactoring Strategy:**

- Extract version file handling to a shared utility
- Create a VersionFile dataclass for type safety
- Centralize version sorting logic

**Implementation:**

```python
# utils/version_file_utils.py
@dataclass
class VersionFile:
    version: str
    mtime: float
    path: Path

def select_newest_version(version_files: list[VersionFile]) -> str:
    """Select the newest version from the list."""
    version_files.sort(
        key=lambda x: (version.parse(x.version.lstrip("v")), x.mtime),
        reverse=True
    )
    return version_files[0].version if version_files else ""
```

**Impact:** Improves type safety and reduces duplication

______________________________________________________________________

## Implementation Priority

### Phase 1: High Impact (Week 1) PASS COMPLETED

1. **Command Validation Pattern** - Base command class PASS
1. **Output Formatter Context Pattern** - Formatter mixin PASS
1. **Error Handling Pattern** - Centralized error display PASS

**Expected Improvement:** 9.94/10 → 9.96/10

### Phase 2: Medium Impact (Week 2) PASS COMPLETED

1. **Table Creation Pattern** - Table factory PASS

**Expected Improvement:** 9.94/10 → 9.95/10

### Phase 3: Low Impact (Week 3) IN PROGRESS

1. **Command Factory Parameters** - InstrumentationParams dataclass (Part 1 Complete)
2. **Version File Handling** - Shared utilities (Deferred - requires more extensive refactoring)

**Expected Improvement:** 9.95/10 → 9.96/10

**Status:** Part 1 complete - InstrumentationParams dataclass created with helper methods in CheckParams and RepositoryParams. Full implementation of using these params throughout the codebase deferred as it requires updating command factory and all CLI handlers.

### Phase 4: Complex Refactoring (Week 4)

1. **Repository URL Handling** - Base repository class

{{ ... }}

**Note:** This refactoring is more complex than initially estimated due to:

- Subtle differences between direct and dynamic download repositories
- Need for extensive testing to ensure no regressions
- Multiple shared methods with slight variations in implementation
- Risk of breaking existing repository functionality

______________________________________________________________________

## Testing Strategy

For each refactoring:

1. **Before Refactoring:**

   - Run full test suite: `task test:all`
   - Record current coverage: `task test:coverage`
   - Run duplication check: `task lint:duplication`

1. **During Refactoring:**

   - Create new utility/base class
   - Update one file at a time
   - Run tests after each file update
   - Verify no functionality changes

1. **After Refactoring:**

   - Run full test suite again
   - Verify coverage maintained or improved
   - Run duplication check to verify reduction
   - Update documentation if needed

______________________________________________________________________

## Success Metrics

- **Duplication Score:** Target 9.99/10 (from current 9.94/10)
- **Lines Reduced:** Estimate 150+ lines of duplicated code removed
- **Maintainability:** Improved through centralized patterns
- **Test Coverage:** Maintained at 61.2% or higher
- **No Regressions:** All 1066 tests continue passing

______________________________________________________________________

## Additional Benefits

1. **Easier Maintenance:** Changes to common patterns only need updates in one place
1. **Consistency:** All commands use the same validation/error handling patterns
1. **Type Safety:** Dataclasses provide better type checking
1. **Documentation:** Centralized utilities are easier to document
1. **Testing:** Shared utilities can be tested once, benefiting all users

______________________________________________________________________

## Notes

- All refactorings should maintain backward compatibility
- Each phase can be done independently
- Focus on high-impact items first
- Consider creating helper utilities in `utils/` directory
- Update documentation as patterns change

______________________________________________________________________

## Related Tasks

- `task lint:duplication` - Check duplication score
- `task metrics` - View overall project metrics
- `task test:all` - Run full test suite
- `task complexity` - Check code complexity

______________________________________________________________________

## Progress Summary

### Completed Phases

**Phase 1: High Impact** PASS

- Command Validation Pattern implemented via BaseCommand class
- Output Formatter Context Pattern implemented via FormatterContextMixin
- Error Handling Pattern implemented via centralized error_display module

**Phase 2: Medium Impact** PASS

- Table Creation Pattern implemented via TableFactory class
- Reduced duplication in table creation across display.py and rich_formatter.py

### In Progress

**Phase 3: Low Impact** - Planned

- Command Factory Parameters refactoring
- Version File Handling utilities

**Phase 4: Complex Refactoring** - Planned

- Repository URL Handling base class (moved from Phase 2 due to complexity)

______________________________________________________________________

**Last Updated:** 2025-10-01
**Status:** Phase 2 Complete, Phase 3 Planned
**Owner:** Development Team
