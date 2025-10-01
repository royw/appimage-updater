# type: ignore
"""Comprehensive unit tests for CLI options definitions."""

from __future__ import annotations

import typer

from appimage_updater.cli.options import CLIOptions
from appimage_updater.ui.output.interface import OutputFormat


class TestGlobalOptions:
    """Tests for global CLI options."""

    def test_debug_option_returns_typer_option(self):
        """Test debug option returns a Typer Option."""
        option = CLIOptions.debug_option()

        assert isinstance(option, typer.models.OptionInfo)

    def test_debug_option_default_false(self):
        """Test debug option defaults to False."""
        option = CLIOptions.debug_option()

        assert option.default is False

    def test_debug_option_has_flag(self):
        """Test debug option has --debug flag."""
        option = CLIOptions.debug_option()

        assert "--debug" in option.param_decls

    def test_debug_option_has_help(self):
        """Test debug option has help text."""
        option = CLIOptions.debug_option()

        assert option.help is not None
        assert "debug" in option.help.lower()

    def test_version_option_returns_typer_option(self):
        """Test version option returns a Typer Option."""
        callback = lambda x: x
        option = CLIOptions.version_option(callback)

        assert isinstance(option, typer.models.OptionInfo)

    def test_version_option_default_false(self):
        """Test version option defaults to False."""
        callback = lambda x: x
        option = CLIOptions.version_option(callback)

        assert option.default is False

    def test_version_option_has_flags(self):
        """Test version option has --version and -V flags."""
        callback = lambda x: x
        option = CLIOptions.version_option(callback)

        assert "--version" in option.param_decls
        assert "-V" in option.param_decls

    def test_version_option_is_eager(self):
        """Test version option is eager."""
        callback = lambda x: x
        option = CLIOptions.version_option(callback)

        assert option.is_eager is True

    def test_version_option_has_callback(self):
        """Test version option has callback."""
        callback = lambda x: x
        option = CLIOptions.version_option(callback)

        assert option.callback == callback


class TestCommonOptions:
    """Tests for common CLI options."""

    def test_config_file_option_is_typer_option(self):
        """Test config file option is a Typer Option."""
        assert isinstance(CLIOptions.CONFIG_FILE_OPTION, typer.models.OptionInfo)

    def test_config_file_option_default_none(self):
        """Test config file option defaults to None."""
        assert CLIOptions.CONFIG_FILE_OPTION.default is None

    def test_config_file_option_has_flags(self):
        """Test config file option has --config and -c flags."""
        assert "--config" in CLIOptions.CONFIG_FILE_OPTION.param_decls
        assert "-c" in CLIOptions.CONFIG_FILE_OPTION.param_decls

    def test_config_dir_option_is_typer_option(self):
        """Test config dir option is a Typer Option."""
        assert isinstance(CLIOptions.CONFIG_DIR_OPTION, typer.models.OptionInfo)

    def test_config_dir_option_has_flags(self):
        """Test config dir option has --config-dir and -d flags."""
        assert "--config-dir" in CLIOptions.CONFIG_DIR_OPTION.param_decls
        assert "-d" in CLIOptions.CONFIG_DIR_OPTION.param_decls

    def test_verbose_option_default_false(self):
        """Test verbose option defaults to False."""
        assert CLIOptions.VERBOSE_OPTION.default is False

    def test_verbose_option_has_flags(self):
        """Test verbose option has --verbose and -v flags."""
        assert "--verbose" in CLIOptions.VERBOSE_OPTION.param_decls
        assert "-v" in CLIOptions.VERBOSE_OPTION.param_decls

    def test_format_option_default_rich(self):
        """Test format option defaults to RICH."""
        assert CLIOptions.FORMAT_OPTION.default == OutputFormat.RICH

    def test_format_option_has_flags(self):
        """Test format option has --format and -f flags."""
        assert "--format" in CLIOptions.FORMAT_OPTION.param_decls
        assert "-f" in CLIOptions.FORMAT_OPTION.param_decls

    def test_format_option_case_insensitive(self):
        """Test format option is case insensitive."""
        assert CLIOptions.FORMAT_OPTION.case_sensitive is False

    def test_dry_run_option_default_false(self):
        """Test dry run option defaults to False."""
        assert CLIOptions.DRY_RUN_OPTION.default is False

    def test_dry_run_option_has_flag(self):
        """Test dry run option has --dry-run flag."""
        assert "--dry-run" in CLIOptions.DRY_RUN_OPTION.param_decls

    def test_yes_option_default_false(self):
        """Test yes option defaults to False."""
        assert CLIOptions.YES_OPTION.default is False

    def test_yes_option_has_flags(self):
        """Test yes option has --yes and -y flags."""
        assert "--yes" in CLIOptions.YES_OPTION.param_decls
        assert "-y" in CLIOptions.YES_OPTION.param_decls

    def test_no_option_default_false(self):
        """Test no option defaults to False."""
        assert CLIOptions.NO_OPTION.default is False

    def test_no_option_has_flags(self):
        """Test no option has --no and -n flags."""
        assert "--no" in CLIOptions.NO_OPTION.param_decls
        assert "-n" in CLIOptions.NO_OPTION.param_decls

    def test_no_interactive_option_default_false(self):
        """Test no interactive option defaults to False."""
        assert CLIOptions.NO_INTERACTIVE_OPTION.default is False

    def test_no_interactive_option_has_flag(self):
        """Test no interactive option has --no-interactive flag."""
        assert "--no-interactive" in CLIOptions.NO_INTERACTIVE_OPTION.param_decls

    def test_create_dir_option_default_false(self):
        """Test create dir option defaults to False."""
        assert CLIOptions.CREATE_DIR_OPTION.default is False

    def test_create_dir_option_has_flag(self):
        """Test create dir option has --create-dir flag."""
        assert "--create-dir" in CLIOptions.CREATE_DIR_OPTION.param_decls


class TestHTTPInstrumentationOptions:
    """Tests for HTTP instrumentation options."""

    def test_instrument_http_option_default_false(self):
        """Test instrument HTTP option defaults to False."""
        assert CLIOptions.INSTRUMENT_HTTP_OPTION.default is False

    def test_instrument_http_option_has_flag(self):
        """Test instrument HTTP option has --instrument-http flag."""
        assert "--instrument-http" in CLIOptions.INSTRUMENT_HTTP_OPTION.param_decls

    def test_http_stack_depth_option_default_4(self):
        """Test HTTP stack depth option defaults to 4."""
        assert CLIOptions.HTTP_STACK_DEPTH_OPTION.default == 4

    def test_http_stack_depth_option_has_min_max(self):
        """Test HTTP stack depth option has min and max constraints."""
        assert CLIOptions.HTTP_STACK_DEPTH_OPTION.min == 1
        assert CLIOptions.HTTP_STACK_DEPTH_OPTION.max == 10

    def test_http_stack_depth_option_has_flag(self):
        """Test HTTP stack depth option has --http-stack-depth flag."""
        assert "--http-stack-depth" in CLIOptions.HTTP_STACK_DEPTH_OPTION.param_decls

    def test_http_track_headers_option_default_false(self):
        """Test HTTP track headers option defaults to False."""
        assert CLIOptions.HTTP_TRACK_HEADERS_OPTION.default is False

    def test_http_track_headers_option_has_flag(self):
        """Test HTTP track headers option has --http-track-headers flag."""
        assert "--http-track-headers" in CLIOptions.HTTP_TRACK_HEADERS_OPTION.param_decls

    def test_trace_option_default_false(self):
        """Test trace option defaults to False."""
        assert CLIOptions.TRACE_OPTION.default is False

    def test_trace_option_has_flag(self):
        """Test trace option has --trace flag."""
        assert "--trace" in CLIOptions.TRACE_OPTION.param_decls


class TestCheckCommandOptions:
    """Tests for check command options."""

    def test_check_app_name_argument_is_argument(self):
        """Test check app name is an Argument."""
        assert isinstance(CLIOptions.CHECK_APP_NAME_ARGUMENT, typer.models.ArgumentInfo)

    def test_check_app_name_argument_default_none(self):
        """Test check app name argument defaults to None."""
        assert CLIOptions.CHECK_APP_NAME_ARGUMENT.default is None

    def test_check_app_name_argument_has_help(self):
        """Test check app name argument has help text."""
        assert CLIOptions.CHECK_APP_NAME_ARGUMENT.help is not None
        assert "application" in CLIOptions.CHECK_APP_NAME_ARGUMENT.help.lower()

    def test_check_info_option_default_false(self):
        """Test check info option defaults to False."""
        assert CLIOptions.CHECK_INFO_OPTION.default is False

    def test_check_info_option_has_flag(self):
        """Test check info option has --info flag."""
        assert "--info" in CLIOptions.CHECK_INFO_OPTION.param_decls


class TestAddCommandOptions:
    """Tests for add command options."""

    def test_add_name_argument_is_argument(self):
        """Test add name is an Argument."""
        assert isinstance(CLIOptions.ADD_NAME_ARGUMENT, typer.models.ArgumentInfo)

    def test_add_name_argument_default_none(self):
        """Test add name argument defaults to None."""
        assert CLIOptions.ADD_NAME_ARGUMENT.default is None

    def test_add_url_argument_is_argument(self):
        """Test add URL is an Argument."""
        assert isinstance(CLIOptions.ADD_URL_ARGUMENT, typer.models.ArgumentInfo)

    def test_add_download_dir_argument_is_argument(self):
        """Test add download dir is an Argument."""
        assert isinstance(CLIOptions.ADD_DOWNLOAD_DIR_ARGUMENT, typer.models.ArgumentInfo)

    def test_add_rotation_option_default_none(self):
        """Test add rotation option defaults to None."""
        assert CLIOptions.ADD_ROTATION_OPTION.default is None

    def test_add_rotation_option_has_flags(self):
        """Test add rotation option has --rotation/--no-rotation flags."""
        param_decls_str = str(CLIOptions.ADD_ROTATION_OPTION.param_decls)
        assert "--rotation" in param_decls_str
        assert "--no-rotation" in param_decls_str

    def test_add_retain_option_default_3(self):
        """Test add retain option defaults to 3."""
        assert CLIOptions.ADD_RETAIN_OPTION.default == 3

    def test_add_retain_option_has_min_max(self):
        """Test add retain option has min and max constraints."""
        assert CLIOptions.ADD_RETAIN_OPTION.min == 1
        assert CLIOptions.ADD_RETAIN_OPTION.max == 10

    def test_add_symlink_option_default_none(self):
        """Test add symlink option defaults to None."""
        assert CLIOptions.ADD_SYMLINK_OPTION.default is None

    def test_add_symlink_option_has_flag(self):
        """Test add symlink option has --symlink-path flag."""
        assert "--symlink-path" in CLIOptions.ADD_SYMLINK_OPTION.param_decls

    def test_add_prerelease_option_default_none(self):
        """Test add prerelease option defaults to None."""
        assert CLIOptions.ADD_PRERELEASE_OPTION.default is None

    def test_add_prerelease_option_has_flags(self):
        """Test add prerelease option has --prerelease/--no-prerelease flags."""
        param_decls_str = str(CLIOptions.ADD_PRERELEASE_OPTION.param_decls)
        assert "--prerelease" in param_decls_str
        assert "--no-prerelease" in param_decls_str

    def test_add_basename_option_default_none(self):
        """Test add basename option defaults to None."""
        assert CLIOptions.ADD_BASENAME_OPTION.default is None

    def test_add_checksum_option_default_none(self):
        """Test add checksum option defaults to None."""
        assert CLIOptions.ADD_CHECKSUM_OPTION.default is None

    def test_add_checksum_option_has_flags(self):
        """Test add checksum option has --checksum/--no-checksum flags."""
        param_decls_str = str(CLIOptions.ADD_CHECKSUM_OPTION.param_decls)
        assert "--checksum" in param_decls_str
        assert "--no-checksum" in param_decls_str

    def test_add_checksum_algorithm_option_default_sha256(self):
        """Test add checksum algorithm option defaults to sha256."""
        assert CLIOptions.ADD_CHECKSUM_ALGORITHM_OPTION.default == "sha256"

    def test_add_checksum_pattern_option_has_default(self):
        """Test add checksum pattern option has default pattern."""
        assert "{filename}" in CLIOptions.ADD_CHECKSUM_PATTERN_OPTION.default

    def test_add_checksum_required_option_default_none(self):
        """Test add checksum required option defaults to None."""
        assert CLIOptions.ADD_CHECKSUM_REQUIRED_OPTION.default is None

    def test_add_pattern_option_default_none(self):
        """Test add pattern option defaults to None."""
        assert CLIOptions.ADD_PATTERN_OPTION.default is None

    def test_add_version_pattern_option_default_none(self):
        """Test add version pattern option defaults to None."""
        assert CLIOptions.ADD_VERSION_PATTERN_OPTION.default is None

    def test_add_direct_option_default_none(self):
        """Test add direct option defaults to None."""
        assert CLIOptions.ADD_DIRECT_OPTION.default is None

    def test_add_direct_option_has_flags(self):
        """Test add direct option has --direct/--no-direct flags."""
        param_decls_str = str(CLIOptions.ADD_DIRECT_OPTION.param_decls)
        assert "--direct" in param_decls_str
        assert "--no-direct" in param_decls_str

    def test_add_auto_subdir_option_default_none(self):
        """Test add auto subdir option defaults to None."""
        assert CLIOptions.ADD_AUTO_SUBDIR_OPTION.default is None

    def test_add_auto_subdir_option_has_flags(self):
        """Test add auto subdir option has --auto-subdir/--no-auto-subdir flags."""
        param_decls_str = str(CLIOptions.ADD_AUTO_SUBDIR_OPTION.param_decls)
        assert "--auto-subdir" in param_decls_str
        assert "--no-auto-subdir" in param_decls_str

    def test_add_interactive_option_default_false(self):
        """Test add interactive option defaults to False."""
        assert CLIOptions.ADD_INTERACTIVE_OPTION.default is False

    def test_add_interactive_option_has_flags(self):
        """Test add interactive option has --interactive and -i flags."""
        assert "--interactive" in CLIOptions.ADD_INTERACTIVE_OPTION.param_decls
        assert "-i" in CLIOptions.ADD_INTERACTIVE_OPTION.param_decls

    def test_add_examples_option_default_false(self):
        """Test add examples option defaults to False."""
        assert CLIOptions.ADD_EXAMPLES_OPTION.default is False

    def test_add_examples_option_has_flag(self):
        """Test add examples option has --examples flag."""
        assert "--examples" in CLIOptions.ADD_EXAMPLES_OPTION.param_decls


class TestEditCommandOptions:
    """Tests for edit command options."""

    def test_edit_app_name_argument_is_argument(self):
        """Test edit app name is an Argument."""
        assert isinstance(CLIOptions.EDIT_APP_NAME_ARGUMENT_OPTIONAL, typer.models.ArgumentInfo)

    def test_edit_app_name_argument_default_none(self):
        """Test edit app name argument defaults to None."""
        assert CLIOptions.EDIT_APP_NAME_ARGUMENT_OPTIONAL.default is None

    def test_edit_url_option_default_none(self):
        """Test edit URL option defaults to None."""
        assert CLIOptions.EDIT_URL_OPTION.default is None

    def test_edit_url_option_has_flag(self):
        """Test edit URL option has --url flag."""
        assert "--url" in CLIOptions.EDIT_URL_OPTION.param_decls

    def test_edit_download_dir_option_default_none(self):
        """Test edit download dir option defaults to None."""
        assert CLIOptions.EDIT_DOWNLOAD_DIR_OPTION.default is None

    def test_edit_basename_option_default_none(self):
        """Test edit basename option defaults to None."""
        assert CLIOptions.EDIT_BASENAME_OPTION.default is None

    def test_edit_pattern_option_default_none(self):
        """Test edit pattern option defaults to None."""
        assert CLIOptions.EDIT_PATTERN_OPTION.default is None

    def test_edit_version_pattern_option_default_none(self):
        """Test edit version pattern option defaults to None."""
        assert CLIOptions.EDIT_VERSION_PATTERN_OPTION.default is None

    def test_edit_enable_option_default_none(self):
        """Test edit enable option defaults to None."""
        assert CLIOptions.EDIT_ENABLE_OPTION.default is None

    def test_edit_enable_option_has_flags(self):
        """Test edit enable option has --enable/--disable flags."""
        param_decls_str = str(CLIOptions.EDIT_ENABLE_OPTION.param_decls)
        assert "--enable" in param_decls_str
        assert "--disable" in param_decls_str

    def test_edit_prerelease_option_default_none(self):
        """Test edit prerelease option defaults to None."""
        assert CLIOptions.EDIT_PRERELEASE_OPTION.default is None

    def test_edit_rotation_option_default_none(self):
        """Test edit rotation option defaults to None."""
        assert CLIOptions.EDIT_ROTATION_OPTION.default is None

    def test_edit_symlink_path_option_default_none(self):
        """Test edit symlink path option defaults to None."""
        assert CLIOptions.EDIT_SYMLINK_PATH_OPTION.default is None

    def test_edit_retain_count_option_default_none(self):
        """Test edit retain count option defaults to None."""
        assert CLIOptions.EDIT_RETAIN_COUNT_OPTION.default is None

    def test_edit_retain_count_option_has_min_max(self):
        """Test edit retain count option has min and max constraints."""
        assert CLIOptions.EDIT_RETAIN_COUNT_OPTION.min == 1
        assert CLIOptions.EDIT_RETAIN_COUNT_OPTION.max == 10

    def test_edit_checksum_option_default_none(self):
        """Test edit checksum option defaults to None."""
        assert CLIOptions.EDIT_CHECKSUM_OPTION.default is None

    def test_edit_checksum_algorithm_option_default_none(self):
        """Test edit checksum algorithm option defaults to None."""
        assert CLIOptions.EDIT_CHECKSUM_ALGORITHM_OPTION.default is None

    def test_edit_checksum_pattern_option_default_none(self):
        """Test edit checksum pattern option defaults to None."""
        assert CLIOptions.EDIT_CHECKSUM_PATTERN_OPTION.default is None

    def test_edit_checksum_required_option_default_none(self):
        """Test edit checksum required option defaults to None."""
        assert CLIOptions.EDIT_CHECKSUM_REQUIRED_OPTION.default is None

    def test_edit_force_option_default_false(self):
        """Test edit force option defaults to False."""
        assert CLIOptions.EDIT_FORCE_OPTION.default is False

    def test_edit_force_option_has_flag(self):
        """Test edit force option has --force flag."""
        assert "--force" in CLIOptions.EDIT_FORCE_OPTION.param_decls

    def test_edit_direct_option_default_none(self):
        """Test edit direct option defaults to None."""
        assert CLIOptions.EDIT_DIRECT_OPTION.default is None

    def test_edit_auto_subdir_option_default_none(self):
        """Test edit auto subdir option defaults to None."""
        assert CLIOptions.EDIT_AUTO_SUBDIR_OPTION.default is None

    def test_edit_dry_run_option_default_false(self):
        """Test edit dry run option defaults to False."""
        assert CLIOptions.EDIT_DRY_RUN_OPTION.default is False


class TestShowCommandOptions:
    """Tests for show command options."""

    def test_show_app_name_argument_is_argument(self):
        """Test show app name is an Argument."""
        assert isinstance(CLIOptions.SHOW_APP_NAME_ARGUMENT_OPTIONAL, typer.models.ArgumentInfo)

    def test_show_app_name_argument_default_none(self):
        """Test show app name argument defaults to None."""
        assert CLIOptions.SHOW_APP_NAME_ARGUMENT_OPTIONAL.default is None

    def test_show_app_name_argument_has_help(self):
        """Test show app name argument has help text."""
        assert CLIOptions.SHOW_APP_NAME_ARGUMENT_OPTIONAL.help is not None


class TestRemoveCommandOptions:
    """Tests for remove command options."""

    def test_remove_app_name_argument_is_argument(self):
        """Test remove app name is an Argument."""
        assert isinstance(CLIOptions.REMOVE_APP_NAME_ARGUMENT_OPTIONAL, typer.models.ArgumentInfo)

    def test_remove_app_name_argument_default_none(self):
        """Test remove app name argument defaults to None."""
        assert CLIOptions.REMOVE_APP_NAME_ARGUMENT_OPTIONAL.default is None

    def test_remove_yes_option_default_false(self):
        """Test remove yes option defaults to False."""
        assert CLIOptions.REMOVE_YES_OPTION.default is False

    def test_remove_yes_option_has_flags(self):
        """Test remove yes option has --yes and -y flags."""
        assert "--yes" in CLIOptions.REMOVE_YES_OPTION.param_decls
        assert "-y" in CLIOptions.REMOVE_YES_OPTION.param_decls

    def test_remove_no_option_default_false(self):
        """Test remove no option defaults to False."""
        assert CLIOptions.REMOVE_NO_OPTION.default is False

    def test_remove_no_option_has_flags(self):
        """Test remove no option has --no and -n flags."""
        assert "--no" in CLIOptions.REMOVE_NO_OPTION.param_decls
        assert "-n" in CLIOptions.REMOVE_NO_OPTION.param_decls


class TestRepositoryCommandOptions:
    """Tests for repository command options."""

    def test_repository_app_name_argument_is_argument(self):
        """Test repository app name is an Argument."""
        assert isinstance(CLIOptions.REPOSITORY_APP_NAME_ARGUMENT, typer.models.ArgumentInfo)

    def test_repository_app_name_argument_has_help(self):
        """Test repository app name argument has help text."""
        assert CLIOptions.REPOSITORY_APP_NAME_ARGUMENT.help is not None

    def test_repository_limit_option_default_10(self):
        """Test repository limit option defaults to 10."""
        assert CLIOptions.REPOSITORY_LIMIT_OPTION.default == 10

    def test_repository_limit_option_has_min_max(self):
        """Test repository limit option has min and max constraints."""
        assert CLIOptions.REPOSITORY_LIMIT_OPTION.min == 1
        assert CLIOptions.REPOSITORY_LIMIT_OPTION.max == 50

    def test_repository_limit_option_has_flags(self):
        """Test repository limit option has --limit and -l flags."""
        assert "--limit" in CLIOptions.REPOSITORY_LIMIT_OPTION.param_decls
        assert "-l" in CLIOptions.REPOSITORY_LIMIT_OPTION.param_decls

    def test_repository_assets_option_default_false(self):
        """Test repository assets option defaults to False."""
        assert CLIOptions.REPOSITORY_ASSETS_OPTION.default is False

    def test_repository_assets_option_has_flags(self):
        """Test repository assets option has --assets and -a flags."""
        assert "--assets" in CLIOptions.REPOSITORY_ASSETS_OPTION.param_decls
        assert "-a" in CLIOptions.REPOSITORY_ASSETS_OPTION.param_decls

    def test_repository_dry_run_option_default_false(self):
        """Test repository dry run option defaults to False."""
        assert CLIOptions.REPOSITORY_DRY_RUN_OPTION.default is False


class TestConfigCommandOptions:
    """Tests for config command options."""

    def test_config_action_argument_is_argument(self):
        """Test config action is an Argument."""
        assert isinstance(CLIOptions.CONFIG_ACTION_ARGUMENT, typer.models.ArgumentInfo)

    def test_config_action_argument_default_empty(self):
        """Test config action argument defaults to empty string."""
        assert CLIOptions.CONFIG_ACTION_ARGUMENT.default == ""

    def test_config_action_argument_has_help(self):
        """Test config action argument has help text."""
        assert CLIOptions.CONFIG_ACTION_ARGUMENT.help is not None
        assert "show" in CLIOptions.CONFIG_ACTION_ARGUMENT.help.lower()

    def test_config_setting_argument_is_argument(self):
        """Test config setting is an Argument."""
        assert isinstance(CLIOptions.CONFIG_SETTING_ARGUMENT, typer.models.ArgumentInfo)

    def test_config_setting_argument_default_empty(self):
        """Test config setting argument defaults to empty string."""
        assert CLIOptions.CONFIG_SETTING_ARGUMENT.default == ""

    def test_config_value_argument_is_argument(self):
        """Test config value is an Argument."""
        assert isinstance(CLIOptions.CONFIG_VALUE_ARGUMENT, typer.models.ArgumentInfo)

    def test_config_value_argument_default_empty(self):
        """Test config value argument defaults to empty string."""
        assert CLIOptions.CONFIG_VALUE_ARGUMENT.default == ""

    def test_config_app_name_option_default_empty(self):
        """Test config app name option defaults to empty string."""
        assert CLIOptions.CONFIG_APP_NAME_OPTION.default == ""

    def test_config_app_name_option_has_flag(self):
        """Test config app name option has --app flag."""
        assert "--app" in CLIOptions.CONFIG_APP_NAME_OPTION.param_decls


class TestOptionConsistency:
    """Tests for consistency across options."""

    def test_all_boolean_options_default_false(self):
        """Test all boolean options default to False unless explicitly set."""
        boolean_options = [
            CLIOptions.VERBOSE_OPTION,
            CLIOptions.DRY_RUN_OPTION,
            CLIOptions.YES_OPTION,
            CLIOptions.NO_OPTION,
            CLIOptions.NO_INTERACTIVE_OPTION,
            CLIOptions.CREATE_DIR_OPTION,
            CLIOptions.INSTRUMENT_HTTP_OPTION,
            CLIOptions.HTTP_TRACK_HEADERS_OPTION,
            CLIOptions.TRACE_OPTION,
            CLIOptions.CHECK_INFO_OPTION,
            CLIOptions.ADD_INTERACTIVE_OPTION,
            CLIOptions.ADD_EXAMPLES_OPTION,
            CLIOptions.EDIT_FORCE_OPTION,
            CLIOptions.EDIT_DRY_RUN_OPTION,
            CLIOptions.REMOVE_YES_OPTION,
            CLIOptions.REMOVE_NO_OPTION,
            CLIOptions.REPOSITORY_ASSETS_OPTION,
            CLIOptions.REPOSITORY_DRY_RUN_OPTION,
        ]

        for option in boolean_options:
            assert option.default is False, f"Option {option.param_decls} should default to False"

    def test_all_options_have_help_text(self):
        """Test all options have help text."""
        # Sample a variety of options
        options_to_check = [
            CLIOptions.CONFIG_FILE_OPTION,
            CLIOptions.VERBOSE_OPTION,
            CLIOptions.FORMAT_OPTION,
            CLIOptions.DRY_RUN_OPTION,
            CLIOptions.ADD_ROTATION_OPTION,
            CLIOptions.EDIT_URL_OPTION,
            CLIOptions.REPOSITORY_LIMIT_OPTION,
        ]

        for option in options_to_check:
            assert option.help is not None, f"Option {option.param_decls} should have help text"
            assert len(option.help) > 0, f"Option {option.param_decls} help text should not be empty"

    def test_short_flags_are_single_character(self):
        """Test short flags are single characters."""
        options_with_short_flags = [
            (CLIOptions.CONFIG_FILE_OPTION, "-c"),
            (CLIOptions.CONFIG_DIR_OPTION, "-d"),
            (CLIOptions.VERBOSE_OPTION, "-v"),
            (CLIOptions.FORMAT_OPTION, "-f"),
            (CLIOptions.YES_OPTION, "-y"),
            (CLIOptions.NO_OPTION, "-n"),
            (CLIOptions.ADD_INTERACTIVE_OPTION, "-i"),
            (CLIOptions.REMOVE_YES_OPTION, "-y"),
            (CLIOptions.REMOVE_NO_OPTION, "-n"),
            (CLIOptions.REPOSITORY_LIMIT_OPTION, "-l"),
            (CLIOptions.REPOSITORY_ASSETS_OPTION, "-a"),
        ]

        for option, short_flag in options_with_short_flags:
            assert short_flag in option.param_decls, f"Option should have {short_flag} flag"
            assert len(short_flag) == 2, f"Short flag {short_flag} should be 2 characters (-X)"

    def test_min_max_constraints_are_valid(self):
        """Test min/max constraints are valid where present."""
        constrained_options = [
            (CLIOptions.HTTP_STACK_DEPTH_OPTION, 1, 10),
            (CLIOptions.ADD_RETAIN_OPTION, 1, 10),
            (CLIOptions.EDIT_RETAIN_COUNT_OPTION, 1, 10),
            (CLIOptions.REPOSITORY_LIMIT_OPTION, 1, 50),
        ]

        for option, expected_min, expected_max in constrained_options:
            assert option.min == expected_min, f"Option {option.param_decls} min should be {expected_min}"
            assert option.max == expected_max, f"Option {option.param_decls} max should be {expected_max}"
            assert option.min < option.max, f"Option {option.param_decls} min should be less than max"


class TestOptionNaming:
    """Tests for option naming conventions."""

    def test_boolean_toggle_options_use_slash_syntax(self):
        """Test boolean toggle options use --flag/--no-flag syntax."""
        toggle_options = [
            CLIOptions.ADD_ROTATION_OPTION,
            CLIOptions.ADD_PRERELEASE_OPTION,
            CLIOptions.ADD_CHECKSUM_OPTION,
            CLIOptions.ADD_CHECKSUM_REQUIRED_OPTION,
            CLIOptions.ADD_DIRECT_OPTION,
            CLIOptions.ADD_AUTO_SUBDIR_OPTION,
            CLIOptions.EDIT_ENABLE_OPTION,
            CLIOptions.EDIT_PRERELEASE_OPTION,
            CLIOptions.EDIT_ROTATION_OPTION,
            CLIOptions.EDIT_CHECKSUM_OPTION,
            CLIOptions.EDIT_CHECKSUM_REQUIRED_OPTION,
            CLIOptions.EDIT_DIRECT_OPTION,
            CLIOptions.EDIT_AUTO_SUBDIR_OPTION,
        ]

        for option in toggle_options:
            # Check that both positive and negative forms exist
            param_decls_str = " ".join(option.param_decls)
            assert "--no-" in param_decls_str or "--disable" in param_decls_str or "--checksum-optional" in param_decls_str, \
                f"Toggle option {option.param_decls} should have negative form"

    def test_argument_names_are_descriptive(self):
        """Test argument names are descriptive."""
        arguments = [
            (CLIOptions.CHECK_APP_NAME_ARGUMENT, "application"),
            (CLIOptions.ADD_NAME_ARGUMENT, "application"),
            (CLIOptions.ADD_URL_ARGUMENT, "URL"),
            (CLIOptions.ADD_DOWNLOAD_DIR_ARGUMENT, "directory"),
            (CLIOptions.CONFIG_ACTION_ARGUMENT, "action"),
            (CLIOptions.CONFIG_SETTING_ARGUMENT, "setting"),
            (CLIOptions.CONFIG_VALUE_ARGUMENT, "value"),
        ]

        for argument, keyword in arguments:
            assert argument.help is not None
            assert keyword.lower() in argument.help.lower(), \
                f"Argument help should mention '{keyword}'"


class TestOptionDefaults:
    """Tests for option default values."""

    def test_numeric_options_have_reasonable_defaults(self):
        """Test numeric options have reasonable default values."""
        numeric_options = [
            (CLIOptions.HTTP_STACK_DEPTH_OPTION, 4),
            (CLIOptions.ADD_RETAIN_OPTION, 3),
            (CLIOptions.REPOSITORY_LIMIT_OPTION, 10),
        ]

        for option, expected_default in numeric_options:
            assert option.default == expected_default, \
                f"Option {option.param_decls} should default to {expected_default}"
            assert option.min <= option.default <= option.max, \
                f"Option {option.param_decls} default should be within min/max range"

    def test_string_options_have_appropriate_defaults(self):
        """Test string options have appropriate defaults."""
        assert CLIOptions.ADD_CHECKSUM_ALGORITHM_OPTION.default == "sha256"
        assert "{filename}" in CLIOptions.ADD_CHECKSUM_PATTERN_OPTION.default

    def test_none_defaults_for_optional_parameters(self):
        """Test None defaults for optional parameters."""
        optional_options = [
            CLIOptions.CONFIG_FILE_OPTION,
            CLIOptions.CONFIG_DIR_OPTION,
            CLIOptions.ADD_ROTATION_OPTION,
            CLIOptions.ADD_SYMLINK_OPTION,
            CLIOptions.ADD_PRERELEASE_OPTION,
            CLIOptions.ADD_BASENAME_OPTION,
            CLIOptions.ADD_PATTERN_OPTION,
            CLIOptions.EDIT_URL_OPTION,
            CLIOptions.EDIT_DOWNLOAD_DIR_OPTION,
        ]

        for option in optional_options:
            assert option.default is None, f"Optional option {option.param_decls} should default to None"
