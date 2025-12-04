# Test Documentation

> **Auto-generated** on 2025-12-04 05:05:43
> **Total Tests**: 326

This page provides a comprehensive overview of all tests in the project, automatically extracted from test docstrings.

## E2E Tests

| Test Class | Test Name | Description |
|------------|-----------|-------------|
| TestAddCommand | `test_add_command_rotation_requires_symlink` | Test add command validates that --rotation requires a symlink path. |
| TestAddCommand | `test_add_command_with_direct_flag` | Test add command with --direct flag sets source_type to 'direct'. |
| TestAddCommand | `test_add_command_with_invalid_url` | Test add command with unknown URL falls back to dynamic download. |
| TestCheckCommandWorkflows | `test_check_command_dry_run_shows_correct_output` | Test that check --dry-run shows proper application data and status. |
| TestCheckCommandWorkflows | `test_check_command_handles_nonexistent_app` | Test that check command handles non-existent applications gracefully. |
| TestCheckCommandWorkflows | `test_check_command_with_format_options` | Test that check command works with different format options. |
| TestE2EFunctionality | `test_check_command_dry_run_no_updates_needed` | Test check command with dry-run when no updates are needed. |
| TestE2EFunctionality | `test_check_command_dry_run_with_updates_available` | Test check command with dry-run when updates are available. |
| TestE2EFunctionality | `test_check_command_with_app_filter` | Test check command with specific app filtering. |
| TestE2EFunctionality | `test_check_command_with_failed_version_check` | Test check command when version check fails. |
| TestE2EFunctionality | `test_check_command_with_invalid_json_config` | Test check command with invalid JSON configuration. |
| TestE2EFunctionality | `test_check_command_with_nonexistent_config` | Test check command with non-existent configuration directory. |
| TestE2EFunctionality | `test_debug_flag_enables_verbose_output` | Test that debug flag enables verbose logging output. |
| TestE2EFunctionality | `test_list_command_truncates_long_paths` | Test that list command properly truncates very long download paths. |
| TestE2EFunctionality | `test_list_command_with_config_directory` | Test list command with directory-based configuration. |
| TestE2EFunctionality | `test_list_command_with_invalid_json_config` | Test list command with invalid JSON configuration. |
| TestE2EFunctionality | `test_list_command_with_multiple_applications` | Test list command with multiple applications (enabled and disabled). |
| TestE2EFunctionality | `test_list_command_with_no_applications` | Test list command with empty configuration. |
| TestE2EFunctionality | `test_list_command_with_nonexistent_config` | Test list command with non-existent configuration directory. |
| TestE2EFunctionality | `test_list_command_with_single_application` | Test list command with a single configured application. |
| TestE2EFunctionality | `test_show_command_case_insensitive` | Test show command with case-insensitive application name matching. |
| TestE2EFunctionality | `test_show_command_with_disabled_application` | Test show command with a disabled application. |
| TestE2EFunctionality | `test_show_command_with_missing_download_directory` | Test show command when download directory doesn't exist. |
| TestE2EFunctionality | `test_show_command_with_no_matching_files` | Test show command when no files match the pattern. |
| TestE2EFunctionality | `test_show_command_with_nonexistent_application` | Test show command with non-existent application. |
| TestE2EFunctionality | `test_show_command_with_symlinks` | Test show command with symlinks present. |
| TestE2EFunctionality | `test_show_command_with_valid_application` | Test show command with a valid application. |
| TestFormatValidationWorkflows | `test_format_option_validation_all_commands` | Test that --format option validation works for all commands. |
| TestFormatValidationWorkflows | `test_html_format_produces_valid_html` | Test that --format html produces valid HTML output. |
| TestFormatValidationWorkflows | `test_invalid_format_option_shows_error` | Test that invalid --format option shows appropriate error. |
| TestFormatValidationWorkflows | `test_json_format_produces_valid_json` | Test that --format json produces valid JSON output. |
| TestFormatValidationWorkflows | `test_plain_format_produces_readable_output` | Test that --format plain produces readable plain text output. |
| TestFormatValidationWorkflows | `test_rich_format_contains_styling` | Test that --format rich contains rich styling elements. |
| TestModernAddCommand | `test_add_duplicate_name_error_modern` | Test that duplicate app names are properly rejected. |
| TestModernAddCommand | `test_add_github_repository_modern` | Test adding a GitHub repository with dependency injection. |
| TestModernAddCommand | `test_add_path_expansion_modern` | Test that user paths are properly expanded. |
| TestModernAddCommand | `test_add_rotation_requires_symlink_modern` | Test that --rotation requires a symlink path. |
| TestModernAddCommand | `test_add_with_direct_flag_modern` | Test adding with --direct flag using modern async architecture. |
| TestModernPatternMatching | `test_pattern_matching_with_suffixes` | Test pattern matching handles various AppImage suffixes correctly. |
| TestModernPatternMatching | `test_pattern_validation_in_config` | Test that pattern validation works correctly in configuration. |
| TestModernRemoveCommand | `test_remove_case_insensitive` | Test that remove command is case insensitive. |
| TestModernRemoveCommand | `test_remove_existing_app_with_confirmation_no` | Test removing an existing application with 'no' confirmation. |
| TestModernRemoveCommand | `test_remove_existing_app_with_confirmation_yes` | Test removing an existing application with 'yes' confirmation. |
| TestModernRemoveCommand | `test_remove_from_multi_app_config` | Test removing one app from a config file with multiple apps. |
| TestModernRemoveCommand | `test_remove_non_interactive` | Test removing an application in non-interactive mode. |
| TestModernRemoveCommand | `test_remove_nonexistent_app` | Test removing a non-existent application. |
| TestModernShowCommand | `test_show_command_with_configured_symlink_path` | Test show command displays symlink path correctly. |
| TestModernShowCommand | `test_show_disabled_application` | Test show command with disabled application. |
| TestModernShowCommand | `test_show_nonexistent_application` | Test show command with non-existent application. |
| TestRemoveCommand | `test_remove_command_empty_config` | Test remove command with empty configuration. |
| TestRemoveCommand | `test_remove_command_from_config_file` | Test remove command removes app from directory-based config. |

## Unit Tests

| Test Class | Test Name | Description |
|------------|-----------|-------------|
| TestAddChecksumDetails | `test_add_checksum_details` | Test adding checksum details. |
| TestAddChecksumStatusLine | `test_disabled_checksum` | Test adding status line for disabled checksum. |
| TestAddChecksumStatusLine | `test_enabled_checksum` | Test adding status line for enabled checksum. |
| TestAddCommand | `test_add_command_examples_mode` | Test add command in examples mode. |
| TestAddCommand | `test_add_command_interactive_mode` | Test add command in interactive mode. |
| TestAddCommand | `test_add_command_validation_missing_name` | Test add command validation with missing name. |
| TestAddCommand | `test_add_command_validation_missing_url` | Test add command validation with missing URL. |
| TestAddCommand | `test_add_command_validation_success` | Test add command validation with valid parameters. |
| TestAddEllipsisIfTruncated | `test_add_ellipsis_if_truncated_empty_result` | Test adding ellipsis to empty result. |
| TestAddEllipsisIfTruncated | `test_add_ellipsis_if_truncated_modifies_in_place` | Test that function modifies the list in place. |
| TestAddEllipsisIfTruncated | `test_add_ellipsis_if_truncated_no_truncation` | Test adding ellipsis when no truncation occurred. |
| TestAddEllipsisIfTruncated | `test_add_ellipsis_if_truncated_with_truncation` | Test adding ellipsis when truncation occurred. |
| TestAddRetainCountLine | `test_with_retain_count` | Test adding retain count line. |
| TestAddRetainCountLine | `test_without_retain_count` | Test not adding retain count line when attribute missing. |
| TestAddRotationStatusLine | `test_disabled_rotation` | Test adding status line for disabled rotation. |
| TestAddRotationStatusLine | `test_enabled_rotation` | Test adding status line for enabled rotation. |
| TestAppConfigs | `test_add_remove_operations` | Test adding and removing application configurations. |
| TestAppConfigs | `test_app_name_filtering` | Test filtering by specific app names. |
| TestAppConfigs | `test_dictionary_access` | Test dictionary-style access by app name. |
| TestAppConfigs | `test_filtering` | Test application filtering functionality. |
| TestAppConfigs | `test_iterator_support` | Test iterator support for app configurations. |
| TestAppConfigsDirectUsage | `test_direct_appconfigs_usage` | Test direct AppConfigs usage with path resolution. |
| TestAppConfigsDirectUsage | `test_path_resolution_logic` | Test that path resolution logic works as expected. |
| TestAssetInfo | `test_asset_info_creation_full` | Test creating AssetInfo with all fields. |
| TestAssetInfo | `test_asset_info_creation_minimal` | Test creating AssetInfo with minimal required fields. |
| TestAssetInfo | `test_asset_info_equality` | Test equality comparison of AssetInfo objects. |
| TestAssetInfo | `test_asset_info_fedora_example` | Test creating AssetInfo for Fedora-specific asset. |
| TestAssetInfo | `test_asset_info_generic_asset` | Test creating AssetInfo for generic asset without distribution info. |
| TestAssetInfo | `test_asset_info_partial_fields` | Test creating AssetInfo with some optional fields. |
| TestAssetInfo | `test_asset_info_repr` | Test string representation of AssetInfo. |
| TestAssetInfo | `test_asset_info_score_range` | Test AssetInfo with different score values. |
| TestAssetInfo | `test_asset_info_with_mock_asset` | Test AssetInfo with mocked Asset for isolation. |
| TestBuildPathFromParts | `test_build_path_from_parts_empty_list` | Test building path from empty parts list. |
| TestBuildPathFromParts | `test_build_path_from_parts_exact_fit` | Test building path that exactly fits the width. |
| TestBuildPathFromParts | `test_build_path_from_parts_multiple_parts_all_fit` | Test building path from multiple parts that all fit. |
| TestBuildPathFromParts | `test_build_path_from_parts_partial_fit` | Test building path from parts where only some fit. |
| TestBuildPathFromParts | `test_build_path_from_parts_preserves_order` | Test that building preserves original order of parts. |
| TestBuildPathFromParts | `test_build_path_from_parts_single_part_fits` | Test building path from single part that fits. |
| TestBuildPathFromParts | `test_build_path_from_parts_single_part_too_long` | Test building path from single part that's too long. |
| TestCheckCommand | `test_check_command_execution` | Test check command execution. |
| TestCheckCommand | `test_check_command_validation` | Test check command validation (no required parameters). |
| TestCollectEditUpdateHelpers | `test_collect_checksum_edit_updates_includes_only_provided_fields` | collect_checksum_edit_updates should only include non-None fields. |
| TestCollectEditUpdateHelpers | `test_collect_rotation_edit_updates_includes_only_provided_fields` | collect_rotation_edit_updates should only include non-None fields. |
| TestCollectEditUpdates | `test_collect_edit_updates_force_default_false` | Test that force defaults to False in collect_edit_updates. |
| TestCollectEditUpdates | `test_collect_edit_updates_passes_force_to_basic` | Test that collect_edit_updates passes force parameter to basic updates. |
| TestCommandFactory | `test_create_add_command` | Test creating an add command. |
| TestCommandFactory | `test_create_check_command_with_instrumentation` | Test creating a check command. |
| TestCommandResult | `test_command_result_failure` | Test failed command result. |
| TestCommandResult | `test_command_result_success` | Test successful command result. |
| TestCompatibilityFunctions | `test_architecture_parsing` | Test architecture extraction from asset filenames. |
| TestCompatibilityFunctions | `test_format_compatibility_non_linux_raises_error` | Test that non-Linux platforms raise RuntimeError. |
| TestCompatibilityFunctions | `test_format_compatibility_windows_raises_error` | Test that Windows platform raises RuntimeError. |
| TestCompatibilityFunctions | `test_format_parsing` | Test file extension extraction from asset filenames. |
| TestCompatibilityFunctions | `test_platform_compatibility_linux_only` | Test platform compatibility checking for Linux only. |
| TestCompatibilityFunctions | `test_platform_compatibility_non_linux_system_raises_error` | Test that non-Linux system platforms raise RuntimeError. |
| TestCompatibilityFunctions | `test_platform_parsing` | Test platform extraction from asset filenames. |
| TestDirectoryConfigLoading | `test_app_configs_loads_global_config` | Test that AppConfigs properly loads global_config from config.json. |
| TestDirectoryConfigLoading | `test_global_defaults_paths_saved_with_tilde_when_under_home` | Global defaults download_dir and symlink_dir should be stored as ~/ paths. |
| TestDirectoryConfigLoading | `test_load_config_from_directory_with_global_config` | Test that \_load_config_from_directory loads both apps and global_config. |
| TestDirectoryConfigLoading | `test_load_config_from_directory_without_global_config` | Test that \_load_config_from_directory uses defaults when config.json missing. |
| TestDirectoryConfigLoading | `test_load_config_with_fallback_uses_global_config_env` | Test \_load_config_with_fallback reading global config via env. |
| TestDirectoryConfigLoading | `test_load_config_with_invalid_global_config_json` | Test that invalid config.json falls back to defaults gracefully. |
| TestDisplayDownloadResults | `test_display_download_results_all_failed` | Test displaying all failed results. |
| TestDisplayDownloadResults | `test_display_download_results_all_successful` | Test displaying all successful results. |
| TestDisplayDownloadResults | `test_display_download_results_empty` | Test displaying empty results list. |
| TestDisplayDownloadResults | `test_display_download_results_mixed` | Test displaying mixed successful and failed results. |
| TestDisplayEditSummary | `test_display_edit_summary` | Test displaying edit summary. |
| TestDisplayFailedDownloads | `test_display_failed_downloads_empty_list` | Test displaying empty failed downloads list. |
| TestDisplayFailedDownloads | `test_display_failed_downloads_multiple_results` | Test displaying multiple failed downloads. |
| TestDisplayFailedDownloads | `test_display_failed_downloads_single_result` | Test displaying single failed download. |
| TestDisplaySuccessfulDownloads | `test_display_successful_downloads_empty_list` | Test displaying empty successful downloads list. |
| TestDisplaySuccessfulDownloads | `test_display_successful_downloads_multiple_results` | Test displaying multiple successful downloads. |
| TestDisplaySuccessfulDownloads | `test_display_successful_downloads_single_result` | Test displaying single successful download. |
| TestDisplaySuccessfulDownloads | `test_display_successful_downloads_with_checksum_warning` | Test displaying successful download with checksum warning. |
| TestDistributionInfo | `test_distribution_info_arch_rolling` | Test creating DistributionInfo for Arch Linux. |
| TestDistributionInfo | `test_distribution_info_creation_full` | Test creating DistributionInfo with all fields. |
| TestDistributionInfo | `test_distribution_info_creation_minimal` | Test creating DistributionInfo with minimal required fields. |
| TestDistributionInfo | `test_distribution_info_equality` | Test equality comparison of DistributionInfo objects. |
| TestDistributionInfo | `test_distribution_info_fedora` | Test creating DistributionInfo for Fedora. |
| TestDistributionInfo | `test_distribution_info_repr` | Test string representation of DistributionInfo. |
| TestDistributionSelector | `test_bambu_studio_scenario` | Test the specific BambuStudio scenario mentioned by user. |
| TestDistributionSelector | `test_calculate_compatibility_score` | Test compatibility score calculation. |
| TestDistributionSelector | `test_convenience_function` | Test the convenience function. |
| TestDistributionSelector | `test_detect_ubuntu_distribution` | Test Ubuntu distribution detection. |
| TestDistributionSelector | `test_is_compatible_distribution` | Test distribution compatibility checking. |
| TestDistributionSelector | `test_is_uncommon_distribution` | Test uncommon distribution detection. |
| TestDistributionSelector | `test_parse_asset_info_ubuntu` | Test parsing Ubuntu asset information. |
| TestDistributionSelector | `test_parse_version_number` | Test version number parsing. |
| TestDistributionSelector | `test_select_best_asset_automatic_selection` | Test automatic asset selection for good matches. |
| TestDistributionSelector | `test_select_best_asset_single_asset` | Test that single asset is returned without analysis. |
| TestEdgeCases | `test_asset_without_parsed_info` | Test assets without architecture/platform information. |
| TestEdgeCases | `test_case_insensitivity` | Test case-insensitive matching. |
| TestEdgeCases | `test_empty_strings` | Test handling of empty strings. |
| TestEdgeCases | `test_unknown_architecture` | Test handling of unknown architectures. |
| TestExtractArchitectureInfo | `test_amd64` | Test extracting amd64 architecture. |
| TestExtractArchitectureInfo | `test_no_match` | Test filename with no architecture match. |
| TestExtractArchitectureInfo | `test_x86_64` | Test extracting x86_64 architecture. |
| TestExtractDistributionInfo | `test_arch_rolling` | Test extracting Arch Linux (rolling release). |
| TestExtractDistributionInfo | `test_fedora_version` | Test extracting Fedora distribution. |
| TestExtractDistributionInfo | `test_ubuntu_version` | Test extracting Ubuntu distribution and version. |
| TestExtractFormatInfo | `test_appimage_format` | Test extracting AppImage format. |
| TestExtractFormatInfo | `test_no_match` | Test filename with no format match. |
| TestExtractFormatInfo | `test_zip_format` | Test extracting ZIP format. |
| TestFixCommandOrphanedInfo | `test_cleanup_orphaned_info_files_empty_directory` | Test cleanup works correctly in empty directory. |
| TestFixCommandOrphanedInfo | `test_cleanup_orphaned_info_files_no_orphaned_files` | Test cleanup works when no orphaned files exist. |
| TestFixCommandOrphanedInfo | `test_cleanup_orphaned_info_files_preserves_valid_files` | Test that valid .current.info files are preserved. |
| TestFixCommandOrphanedInfo | `test_cleanup_orphaned_info_files_removes_orphaned_files` | Test that orphaned .current.info files are removed. |
| TestFixCommandOrphanedInfo | `test_cleanup_orphaned_info_files_with_different_extensions` | Test cleanup only processes .current.info files, not other .info files. |
| TestGetAppConfigPath | `test_directory_config` | Test getting config path for directory-based config. |
| TestGetAppConfigPath | `test_file_config` | Test getting config path for file-based config. |
| TestGetAppConfigPath | `test_unknown_config_type` | Test getting config path for unknown config type. |
| TestGetBaseAppImageName | `test_complex_filename` | Test complex filename with rotation suffix. |
| TestGetBaseAppImageName | `test_current_suffix` | Test filename with .current suffix. |
| TestGetBaseAppImageName | `test_no_rotation_suffix` | Test filename without rotation suffix. |
| TestGetBaseAppImageName | `test_old_numbered_suffix` | Test filename with numbered .old suffix. |
| TestGetBaseAppImageName | `test_old_suffix` | Test filename with .old suffix. |
| TestGetBasicConfigLines | `test_disabled_app` | Test basic config lines for disabled app. |
| TestGetBasicConfigLines | `test_enabled_app` | Test basic config lines for enabled app. |
| TestGetChecksumStatus | `test_get_checksum_status_falsy_checksum_result` | Test checksum status when checksum verified is None. |
| TestGetChecksumStatus | `test_get_checksum_status_no_checksum_result` | Test checksum status when no checksum verified attribute is available. |
| TestGetChecksumStatus | `test_get_checksum_status_no_verified_attribute` | Test checksum status when verified attribute is missing. |
| TestGetChecksumStatus | `test_get_checksum_status_not_verified` | Test checksum status when checksum is not verified. |
| TestGetChecksumStatus | `test_get_checksum_status_verified` | Test checksum status when checksum is verified. |
| TestGetEffectiveChecksumConfig | `test_defaults_when_all_values_none_and_no_defaults` | Without explicit values or defaults, built-in checksum defaults are used. |
| TestGetEffectiveChecksumConfig | `test_explicit_values_override_defaults` | Explicit checksum parameters should override defaults when provided. |
| TestGetEffectiveDownloadDir | `test_current_working_directory_used_when_no_defaults` | Without download_dir or defaults, use Path.cwd() / name. |
| TestGetEffectiveDownloadDir | `test_defaults_used_when_no_download_dir` | When no download_dir is given, use defaults.get_default_download_dir(name). |
| TestGetEffectiveDownloadDir | `test_explicit_download_dir_is_used_as_is` | If download_dir is provided, it should be returned unchanged. |
| TestGetRotationIndicator | `test_current_indicator` | Test filename with current indicator. |
| TestGetRotationIndicator | `test_no_indicator` | Test filename without rotation indicator. |
| TestGetRotationIndicator | `test_old_indicator` | Test filename with old indicator. |
| TestGetSymlinksInfo | `test_no_symlink_configured` | Test app with no symlink configured. |
| TestGetSymlinksInfo | `test_none_symlink_path` | Test app with None symlink path. |
| TestGetSymlinksInfo | `test_path_not_symlink` | Test path with found symlinks. |
| TestGetSymlinksInfo | `test_symlink_does_not_exist` | Test when download directory doesn't exist. |
| TestGitHubAuth | `test_appimage_updater_token_environment_variable` | Test token discovery from app-specific environment variable. |
| TestGitHubAuth | `test_environment_variable_priority` | Test that GITHUB_TOKEN takes priority over app-specific token. |
| TestGitHubAuth | `test_explicit_token_overrides_discovery` | Test that explicit token parameter overrides auto-discovery. |
| TestGitHubAuth | `test_factory_function_with_discovery` | Test factory function with token discovery. |
| TestGitHubAuth | `test_factory_function_with_explicit_token` | Test factory function with explicit token. |
| TestGitHubAuth | `test_file_read_error_handling` | Test graceful handling of file read errors. |
| TestGitHubAuth | `test_get_auth_headers_anonymous` | Test auth headers generation without authentication. |
| TestGitHubAuth | `test_get_auth_headers_authenticated` | Test auth headers generation with authentication. |
| TestGitHubAuth | `test_github_token_environment_variable` | Test token discovery from GITHUB_TOKEN environment variable. |
| TestGitHubAuth | `test_global_config_alternative_token_locations` | Test token discovery from alternative locations in global config. |
| TestGitHubAuth | `test_global_config_token_discovery` | Test token discovery from global config file. |
| TestGitHubAuth | `test_no_token_found` | Test behavior when no token is found anywhere. |
| TestGitHubAuth | `test_rate_limit_info_anonymous` | Test rate limit information for anonymous requests. |
| TestGitHubAuth | `test_rate_limit_info_authenticated` | Test rate limit information for authenticated requests. |
| TestGitHubAuth | `test_token_file_alternative_json_key` | Test token discovery from JSON file with alternative key name. |
| TestGitHubAuth | `test_token_file_json_format` | Test token discovery from JSON token file. |
| TestGitHubAuth | `test_token_file_plain_text_format` | Test token discovery from plain text token file. |
| TestGitHubClientAuthentication | `test_client_with_auto_discovery` | Test GitHubClient with automatic token discovery. |
| TestGitHubClientAuthentication | `test_client_with_explicit_auth` | Test GitHubClient with explicit GitHubAuth instance. |
| TestGitHubClientAuthentication | `test_client_with_explicit_token` | Test GitHubClient with explicit token parameter. |
| TestGlobalConfigManager | `test_default_properties` | Test default configuration properties. |
| TestGlobalConfigManager | `test_property_access` | Test property-based access to global configuration. |
| TestHasChecksumConfig | `test_falsy_checksum` | Test app with falsy checksum. |
| TestHasChecksumConfig | `test_has_checksum_config` | Test app with checksum config. |
| TestHasChecksumConfig | `test_no_checksum_attribute` | Test app without checksum attribute. |
| TestHasRotationSuffix | `test_current_suffix` | Test filename with .current suffix. |
| TestHasRotationSuffix | `test_no_suffix` | Test filename without rotation suffix. |
| TestHasRotationSuffix | `test_old_numbered_suffix` | Test filename with numbered .old suffix. |
| TestHasRotationSuffix | `test_old_suffix` | Test filename with .old suffix. |
| TestIsMatchingAppImageFile | `test_matching_file` | Test file that matches pattern. |
| TestIsMatchingAppImageFile | `test_non_file` | Test directory (not a file). |
| TestIsMatchingAppImageFile | `test_non_matching_pattern` | Test file that doesn't match pattern. |
| TestIsMatchingAppImageFile | `test_symlink` | Test symlink file. |
| TestManager | `test_load_config_method` | Test that Manager.load_config method works with directory-based config. |
| TestMigrationBenefits | `test_consistent_architecture_handling` | Test that architecture handling is consistent across all operations. |
| TestMigrationBenefits | `test_consistent_git_hash_handling` | Test that git hash handling is consistent across all operations. |
| TestMigrationBenefits | `test_single_source_of_truth` | Test that there's now a single source of truth for version operations. |
| TestParseAssetInfo | `test_parse_generic_no_info` | Test parsing generic asset with no distribution info. |
| TestParseAssetInfo | `test_parse_ubuntu_complete` | Test parsing Ubuntu asset with complete information. |
| TestParseVersionNumber | `test_decimal_version` | Test parsing decimal version numbers. |
| TestParseVersionNumber | `test_integer_version` | Test parsing integer version numbers. |
| TestParseVersionNumber | `test_invalid_version` | Test parsing invalid version strings. |
| TestPrereleaseAutoDetection | `test_add_command_auto_enables_prerelease` | Test that add command automatically enables prerelease for continuous build repos. |
| TestPrereleaseAutoDetection | `test_add_command_does_not_auto_enable_prerelease_for_stable` | Test that add command does not auto-enable prerelease for repos with stable releases. |
| TestPrereleaseAutoDetection | `test_add_command_respects_explicit_no_prerelease_setting` | Test that add command respects explicitly set --no-prerelease flag even with auto-detection. |
| TestPrereleaseAutoDetection | `test_add_command_respects_explicit_prerelease_setting` | Test that add command respects explicitly set --prerelease flag even with auto-detection. |
| TestPromptUserSelection | `test_prompt_user_selection_default_choice` | Test using default choice (empty input). |
| TestPromptUserSelection | `test_prompt_user_selection_eof_error_handling` | Test handling of EOFError (non-interactive environment). |
| TestPromptUserSelection | `test_prompt_user_selection_invalid_then_valid` | Test invalid choice followed by valid choice. |
| TestPromptUserSelection | `test_prompt_user_selection_keyboard_interrupt_handling` | Test handling of KeyboardInterrupt (Ctrl+C). |
| TestPromptUserSelection | `test_prompt_user_selection_multiple_retries` | Test multiple invalid attempts before valid selection. |
| TestPromptUserSelection | `test_prompt_user_selection_negative_invalid` | Test that negative numbers are treated as invalid. |
| TestPromptUserSelection | `test_prompt_user_selection_single_asset` | Test selection with only one asset. |
| TestPromptUserSelection | `test_prompt_user_selection_table_creation` | Test that table is created and displayed correctly. |
| TestPromptUserSelection | `test_prompt_user_selection_valid_choice_first` | Test selecting the first asset. |
| TestPromptUserSelection | `test_prompt_user_selection_valid_choice_second` | Test selecting the second asset. |
| TestPromptUserSelection | `test_prompt_user_selection_value_error_handling` | Test handling of non-numeric input. |
| TestPromptUserSelection | `test_prompt_user_selection_zero_invalid` | Test that zero is treated as invalid choice. |
| TestReleaseFiltering | `test_compatibility_filtering` | Test compatibility filtering (mock system info). |
| TestReleaseFiltering | `test_pattern_matching_no_filter` | Test basic pattern matching without filtering. |
| TestReplaceHomeWithTilde | `test_replace_home_with_tilde_empty_string` | Test replacing home in empty string. |
| TestReplaceHomeWithTilde | `test_replace_home_with_tilde_exact_home` | Test replacing exact home directory. |
| TestReplaceHomeWithTilde | `test_replace_home_with_tilde_home_nested_subdir` | Test replacing home nested subdirectory. |
| TestReplaceHomeWithTilde | `test_replace_home_with_tilde_home_subdir` | Test replacing home subdirectory. |
| TestReplaceHomeWithTilde | `test_replace_home_with_tilde_no_separator` | Test replacing home when path continues without separator. |
| TestReplaceHomeWithTilde | `test_replace_home_with_tilde_none_like` | Test replacing home with falsy string. |
| TestReplaceHomeWithTilde | `test_replace_home_with_tilde_not_home_path` | Test not replacing non-home paths. |
| TestReplaceHomeWithTilde | `test_replace_home_with_tilde_similar_path` | Test replacing similar paths - actually does replace. |
| TestRepositoryFactory | `test_get_repository_client_direct_with_github_url` | Test --direct flag behavior with GitHub URL. |
| TestRepositoryFactory | `test_get_repository_client_github_url_detection_fallback` | Test get_repository_client falls back to URL detection for GitHub URLs. |
| TestRepositoryFactory | `test_get_repository_client_invalid_source_type` | Test error handling for invalid source_type. |
| TestRepositoryFactory | `test_get_repository_client_non_github_url_detection_fallback` | Test fallback to DirectDownloadRepository for non-GitHub URLs. |
| TestRepositoryFactory | `test_get_repository_client_preserves_url_exactly` | Test that repository client preserves URL exactly as provided. |
| TestRepositoryFactory | `test_get_repository_client_source_type_precedence_over_url_detection` | Test that explicit source_type takes precedence over URL detection. |
| TestRepositoryFactory | `test_get_repository_client_with_direct_download_source_type` | Test get_repository_client with explicit source_type='direct_download'. |
| TestRepositoryFactory | `test_get_repository_client_with_dynamic_download_source_type` | Test get_repository_client with explicit source_type='dynamic_download'. |
| TestRepositoryFactory | `test_get_repository_client_with_explicit_github_source_type` | Test get_repository_client with explicit source_type='github'. |
| TestRepositoryFactoryIntegration | `test_configuration_with_direct_source_type` | Test repository client creation from configuration with direct source type. |
| TestRepositoryFactoryIntegration | `test_configuration_with_github_source_type` | Test configuration scenario with source_type='github'. |
| TestRepositoryFactoryIntegration | `test_legacy_configuration_without_source_type` | Test legacy configuration without explicit source_type field. |
| TestRepositoryFactoryIntegration | `test_mixed_configuration_scenarios` | Test various configuration scenarios that might occur in practice. |
| TestResultsDisplayIntegration | `test_console_initialization` | Test that console is properly initialized. |
| TestResultsDisplayIntegration | `test_console_no_color_environment` | Test console respects NO_COLOR environment variable. |
| TestSymlinkPathValidators | `test_validate_symlink_path_characters_accepts_normal_paths` | Regular filesystem paths should be accepted. |
| TestSymlinkPathValidators | `test_validate_symlink_path_characters_rejects_invalid_chars` | Paths containing NUL or newline characters should be rejected. |
| TestSymlinkPathValidators | `test_validate_symlink_path_exists_allows_non_empty` | Non-empty paths should pass existence check. |
| TestSymlinkPathValidators | `test_validate_symlink_path_exists_rejects_empty_or_whitespace` | Empty or whitespace-only symlink paths should raise ValueError. |
| TestSymlinkPathValidators | `test_validate_symlink_path_noop_when_missing_key` | If 'symlink_path' is not present, validate_symlink_path should be a no-op. |
| TestSymlinkPathValidators | `test_validate_symlink_path_rejects_non_appimage_extension` | Non-.AppImage symlink paths should be rejected by the full validator. |
| TestSymlinkPathValidators | `test_validate_symlink_path_updates_to_normalized_absolute` | validate_symlink_path should normalize and store an absolute .AppImage path. |
| TestSystemDetector | `test_architecture_detection` | Test architecture detection and aliasing. |
| TestSystemDetector | `test_format_detection_darwin_raises_error` | Test that non-Linux platforms raise RuntimeError. |
| TestSystemDetector | `test_format_detection_linux` | Test supported format detection for Linux. |
| TestSystemDetector | `test_format_detection_windows_raises_error` | Test that non-Linux platforms raise RuntimeError. |
| TestSystemDetector | `test_platform_detection` | Test platform detection. |
| TestUnifiedRepositoryInterface | `test_enhanced_function_still_works` | Test that enhanced function still works independently. |
| TestUnifiedRepositoryInterface | `test_legacy_function_still_works` | Test that legacy function still works independently. |
| TestUnifiedRepositoryInterface | `test_unified_interface_async_enhanced_path` | Test async version uses enhanced path with probing enabled (sync wrapper test). |
| TestUnifiedRepositoryInterface | `test_unified_interface_async_version` | Test async version of unified interface (sync wrapper test). |
| TestUnifiedRepositoryInterface | `test_unified_interface_backward_compatibility` | Test that unified interface maintains backward compatibility. |
| TestUnifiedRepositoryInterface | `test_unified_interface_default_behavior` | Test unified interface default behavior (probing enabled by default). |
| TestUnifiedRepositoryInterface | `test_unified_interface_enhanced_path_github` | Test unified interface uses enhanced path for GitHub with probing enabled. |
| TestUnifiedRepositoryInterface | `test_unified_interface_enhanced_path_unknown_domain` | Test unified interface uses enhanced path for unknown domains. |
| TestUnifiedRepositoryInterface | `test_unified_interface_explicit_source_type_overrides_probing` | Test that explicit source_type overrides probing behavior. |
| TestUnifiedRepositoryInterface | `test_unified_interface_legacy_path_direct` | Test unified interface uses legacy path for direct URLs with probing disabled. |
| TestUnifiedRepositoryInterface | `test_unified_interface_legacy_path_github` | Test unified interface uses legacy path for GitHub with probing disabled. |
| TestUnifiedRepositoryInterface | `test_unified_interface_performance_optimization` | Test performance optimization scenarios. |
| TestValidateAddRotationConfig | `test_rotation_none_or_false_is_allowed` | Rotation disabled or unspecified should pass validation. |
| TestValidateAddRotationConfig | `test_rotation_true_without_symlink_shows_error_and_returns_false` | --rotation without symlink should be rejected with helpful messaging. |
| TestValidateBasicFieldUpdates | `test_invalid_checksum_algorithm_raises_value_error` | An unsupported checksum_algorithm should raise ValueError. |
| TestValidateBasicFieldUpdates | `test_invalid_regex_pattern_raises_value_error` | An invalid regex pattern in updates['pattern'] should raise ValueError. |
| TestValidateBasicFieldUpdates | `test_valid_pattern_and_checksum_algorithm_pass_validation` | Valid regex pattern and checksum algorithm should not raise. |
| TestValidateBasicFieldUpdates | `test_validate_direct_url_handles_exceptions` | Non-string or malformed inputs should be caught and return None with details. |
| TestValidateDirectUrl | `test_validate_direct_url_accepts_well_formed_url` | A well-formed URL with scheme and host should be returned unchanged. |
| TestValidateDirectUrl | `test_validate_direct_url_rejects_missing_scheme_or_host` | URLs without scheme or host should be rejected with an error message. |
| TestValidateUrlUpdate | `test_validate_url_update_force_bypasses_validation_errors` | Test that force flag bypasses validation errors completely. |
| TestValidateUrlUpdate | `test_validate_url_update_force_removes_flag_from_updates` | Test that force flag is removed from updates after processing. |
| TestValidateUrlUpdate | `test_validate_url_update_no_url_returns_early` | Test that validate_url_update returns early when no URL is provided. |
| TestValidateUrlUpdate | `test_validate_url_update_validation_error_propagates` | Test that validation errors are properly propagated when not using force. |
| TestValidateUrlUpdate | `test_validate_url_update_with_force_skips_validation` | Test that validate_url_update skips validation when force=True. |
| TestValidateUrlUpdate | `test_validate_url_update_without_force_flag_performs_validation` | Test validation when force flag is not present (defaults to False). |
| TestValidateUrlUpdate | `test_validate_url_update_without_force_performs_validation` | Test that validate_url_update performs normal validation when force=False. |
| TestVersionChecker | `test_version_checker_initialization` | Test that VersionChecker can be initialized. |
| TestVersionServicesIntegration | `test_backward_compatibility_maintained` | Test that the migration maintains backward compatibility. |
| TestVersionServicesIntegration | `test_info_file_operations` | Test info file service operations. |
| TestVersionServicesIntegration | `test_pattern_generation_creates_flexible_patterns` | Test that pattern generation creates flexible, reusable patterns. |
| TestVersionServicesIntegration | `test_services_integration_consistency` | Test that all services work together consistently. |
| TestVersionServicesIntegration | `test_version_comparison_logic` | Test centralized version comparison logic. |
| TestVersionServicesIntegration | `test_version_extraction_excludes_git_hashes` | Test that version extraction properly excludes git commit hashes. |
| TestVersionServicesIntegration | `test_version_normalization_consistency` | Test that version normalization is consistent. |
| TestWrapPath | `test_wrap_path_default_max_width` | Test wrapping path with default max width. |
| TestWrapPath | `test_wrap_path_empty_string` | Test wrapping empty path. |
| TestWrapPath | `test_wrap_path_exact_max_width` | Test wrapping path that's exactly at max width. |
| TestWrapPath | `test_wrap_path_integration_with_home_replacement` | Test integration between path wrapping and home replacement. |
| TestWrapPath | `test_wrap_path_long_path_with_separators` | Test wrapping long path with separators. |
| TestWrapPath | `test_wrap_path_no_separators_fallback` | Test wrapping path with no separators (fallback to truncation). |
| TestWrapPath | `test_wrap_path_root_with_file` | Test wrapping root path with file. |
| TestWrapPath | `test_wrap_path_short_path` | Test wrapping path that's already short enough. |
| TestWrapPath | `test_wrap_path_single_separator` | Test wrapping path with single separator. |
| TestWrapPath | `test_wrap_path_windows_separators` | Test wrapping path with Windows separators. |
