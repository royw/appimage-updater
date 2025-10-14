# Formatter Audit Checklist

This checklist tracks the audit of all commands to ensure they properly use the output formatter's console for consistent color support across Rich, Plain, and Markdown formats.

## Status Legend
- ✅ **Done**: Command properly uses output formatter's console
- ⚠️ **Needs Review**: Command may need updates
- ❌ **Not Done**: Command needs to be updated
- 🔍 **In Progress**: Currently being worked on
- N/A: Command doesn't use console output

## Commands to Audit

### Config Commands
- [x] ✅ `config list` - Uses formatter's console (completed)
- [x] ✅ `config show` - Uses formatter's console (completed)
- [x] ✅ `config show-effective` - Uses formatter's console (completed)
- [ ] ❌ `config set` - Still uses module-level console for success/error messages
- [ ] ❌ `config reset` - Still uses module-level console for messages

### Application Management Commands
- [ ] ❌ `add` - Check if uses output formatter
- [ ] ❌ `edit` - Check if uses output formatter
- [ ] ❌ `remove` - Check if uses output formatter
- [ ] ❌ `enable` - Check if uses output formatter
- [ ] ❌ `disable` - Check if uses output formatter

### Query Commands
- [ ] ❌ `list` - Check if uses output formatter (likely already correct)
- [ ] ❌ `show` - Check if uses output formatter
- [ ] ❌ `check` - Check if uses output formatter
- [ ] ❌ `repository` - Check if uses output formatter

### Update Commands
- [ ] ❌ `update` - Check if uses output formatter
- [ ] ❌ `download` - Check if uses output formatter

### Utility Commands
- [ ] ❌ `version` - Check if uses output formatter
- [ ] N/A `help` - Built-in Typer functionality

## Files to Review

### Primary Command Files
- [ ] `src/appimage_updater/cli/handlers/add_handler.py`
- [ ] `src/appimage_updater/cli/handlers/check_handler.py`
- [ ] `src/appimage_updater/cli/handlers/download_handler.py`
- [ ] `src/appimage_updater/cli/handlers/edit_handler.py`
- [ ] `src/appimage_updater/cli/handlers/enable_disable_handler.py`
- [ ] `src/appimage_updater/cli/handlers/list_handler.py`
- [ ] `src/appimage_updater/cli/handlers/remove_handler.py`
- [ ] `src/appimage_updater/cli/handlers/repository_handler.py`
- [ ] `src/appimage_updater/cli/handlers/show_handler.py`
- [ ] `src/appimage_updater/cli/handlers/update_handler.py`

### Display/Output Files
- [ ] `src/appimage_updater/ui/display.py` - Module-level console usage
- [ ] `src/appimage_updater/ui/cli/display_utilities.py` - Module-level console usage
- [ ] `src/appimage_updater/ui/cli/error_handling.py` - Module-level console usage
- [ ] `src/appimage_updater/ui/cli/validation_utilities.py` - Module-level console usage
- [ ] `src/appimage_updater/ui/error_display.py` - Module-level console usage

### Config-Related Files
- [x] ✅ `src/appimage_updater/config/command.py` - Partially updated
- [ ] ⚠️ `src/appimage_updater/config/cmd/display_utilities.py` - Module-level console
- [ ] ⚠️ `src/appimage_updater/config/cmd/error_handling.py` - Module-level console
- [ ] ⚠️ `src/appimage_updater/config/cmd/setting_operations.py` - Module-level console
- [ ] ⚠️ `src/appimage_updater/config/operations.py` - Module-level console

### Core Operation Files
- [ ] `src/appimage_updater/core/update_operations.py` - Module-level console usage

## Audit Process

For each command/file:

1. **Identify Console Usage**
   - [ ] Search for `console = Console(` patterns
   - [ ] Search for `console.print(` calls
   - [ ] Identify if using module-level or formatter's console

2. **Check Output Formatter Support**
   - [ ] Verify command accepts `output_format` parameter
   - [ ] Check if `get_output_formatter()` is called
   - [ ] Verify formatter's console is passed to display functions

3. **Test Color Output**
   - [ ] Test with `--format rich` (default)
   - [ ] Test with `--format plain`
   - [ ] Test with `--format markdown`
   - [ ] Verify colors work in actual terminal (not piped)

4. **Update if Needed**
   - [ ] Add console parameter to display functions
   - [ ] Pass formatter's console to functions
   - [ ] Update tests to match new signatures
   - [ ] Verify all tests pass

## Common Patterns to Fix

### Pattern 1: Module-Level Console
```python
# ❌ Bad - Module-level console
console = Console(no_color=bool(os.environ.get("NO_COLOR")))

def some_function():
    console.print("[green]Success!")
```

### Pattern 2: Using Formatter's Console
```python
# ✅ Good - Using formatter's console
def some_function(rich_console: Console | None = None):
    console_to_use = rich_console or console
    console_to_use.print("[green]Success!")

# In command handler:
formatter = get_output_formatter()
rich_console = formatter.console if formatter and hasattr(formatter, "console") else console
some_function(rich_console)
```

## Priority Order

1. **High Priority** - User-facing output commands
   - [ ] `list`, `show`, `check` - Most frequently used
   - [ ] `update`, `download` - Critical functionality
   - [ ] `add`, `remove`, `edit` - Configuration management

2. **Medium Priority** - Configuration commands
   - [ ] `config set`, `config reset` - Success/error messages
   - [ ] `enable`, `disable` - Status messages

3. **Low Priority** - Internal utilities
   - [ ] Error handling utilities
   - [ ] Validation utilities
   - [ ] Display utilities

## Testing Strategy

After each command is updated:

1. **Unit Tests**
   - [ ] Update test mocks to accept console parameter
   - [ ] Verify function signatures match
   - [ ] Run: `uv run pytest tests/unit/ -v`

2. **Integration Tests**
   - [ ] Test command with all format options
   - [ ] Verify colors display correctly
   - [ ] Run: `uv run pytest tests/e2e/ -v`

3. **Manual Testing**
   - [ ] Run command in actual terminal (konsole, gnome-terminal, etc.)
   - [ ] Verify colors appear correctly
   - [ ] Test with `--format markdown` and view in GitHub

## Notes

- The `list` command already uses output formatter correctly (verified working)
- Config commands (`list`, `show`, `show-effective`) now use formatter's console
- Module-level console usage is acceptable for error handling that doesn't need formatting
- Focus on commands that produce structured output (tables, lists, etc.)

## Completion Criteria

- [ ] All high-priority commands audited and updated
- [ ] All medium-priority commands audited and updated
- [ ] All tests passing (2126+ tests)
- [ ] Code coverage maintained (74%+)
- [ ] All lint checks passing
- [ ] Documentation updated if needed
- [ ] CHANGELOG.md updated with changes

## Related Issues

- Original issue: `config list` colors not working in konsole
- Root cause: Module-level console vs formatter's console
- Solution: Pass formatter's console to display functions

## Progress Tracking

- **Started**: 2025-10-14
- **Config commands completed**: 2025-10-14
- **Estimated completion**: TBD
- **Commands completed**: 3/15 (20%)
- **Files reviewed**: 1/15 (7%)
