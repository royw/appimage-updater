#!/usr/bin/env python3

# -------------------------------------------------------------------------
#                                                                         -
#  Python Module Argument Parser                                          -
#                                                                         -
#  Created by Fonic <https://github.com/fonic>                            -
#  Date: 06/20/19 - 04/03/24                                              -
#  https://gist.github.com/fonic/fe6cade2e1b9eaf3401cc732f48aeebd
#                                                                        -
# -------------------------------------------------------------------------

from __future__ import annotations

import argparse
import os
import shutil
import sys
import textwrap
from typing import TYPE_CHECKING, Any, Never


if TYPE_CHECKING:
    from _typeshed import SupportsWrite

SUPPRESS = argparse.SUPPRESS


# Custom argument group that handles pyproject_key
class _ArgumentGroup(argparse._ArgumentGroup):
    """Custom argument group that extracts pyproject_key before passing to parent."""

    def __init__(self, container: Any, *args: Any, **kwargs: Any) -> None:
        super().__init__(container, *args, **kwargs)
        # Store reference to the parser for later use
        self._parser = container

    def add_argument(self, *args: Any, **kwargs: Any) -> argparse.Action:
        # Extract custom parameters that argparse doesn't recognize
        pyproject_key = kwargs.pop("pyproject_key", None)

        action = super().add_argument(*args, **kwargs)

        # Build argument dict for our tracking
        argument: dict[str, Any] = {key: kwargs[key] for key in kwargs}
        if pyproject_key is not None:
            argument["pyproject_key"] = pyproject_key

        # Get the parser (stored during __init__)
        parser = self._parser

        # Positional: argument with only one name not starting with '-'
        if len(args) == 0 or (len(args) == 1 and isinstance(args[0], str) and not args[0].startswith("-")):
            argument["name"] = args[0] if (len(args) > 0) else argument.get("dest", "")
            if hasattr(parser, "positionals"):
                parser.positionals.append(argument)
        else:
            # Option: argument with flags starting with '-'
            argument["flags"] = list(args)
            if hasattr(parser, "options"):
                parser.options.append(argument)

        return action


# ArgumentParser class providing custom help/usage output
class CustomArgumentParser(argparse.ArgumentParser):
    # Expose argparse.SUPPRESS as a class attribute for convenience
    SUPPRESS = argparse.SUPPRESS

    # Postition of 'width' argument: https://www.python.org/dev/peps/pep-3102/
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # At least self.positionals + self.options need to be initialized before calling
        # __init__() of parent class, as argparse.ArgumentParser.__init__() defaults to
        # 'add_help=True', which results in call of add_argument("-h", "--help", ...)
        self.program: dict[str, Any] = {key: kwargs[key] for key in kwargs}
        self.positionals: list[dict[str, Any]] = []
        self.options: list[dict[str, Any]] = []
        self.width: int = shutil.get_terminal_size().columns or 80
        super().__init__(*args, **kwargs)

    def add_argument_group(self, *args: Any, **kwargs: Any) -> _ArgumentGroup:
        """Override to return our custom argument group that handles pyproject_key."""
        group = _ArgumentGroup(self, *args, **kwargs)
        self._action_groups.append(group)
        return group

    def add_argument(self, *args: Any, **kwargs: Any) -> argparse.Action:
        # Extract custom parameters that argparse doesn't recognize
        pyproject_key = kwargs.pop("pyproject_key", None)

        action = super().add_argument(*args, **kwargs)
        argument: dict[str, Any] = {key: kwargs[key] for key in kwargs}

        # Add back custom parameters to our argument dict
        if pyproject_key is not None:
            argument["pyproject_key"] = pyproject_key

        # Positional: argument with only one name not starting with '-' provided as
        # positional argument to method -or- no name and only a 'dest=' argument
        if len(args) == 0 or (len(args) == 1 and isinstance(args[0], str) and not args[0].startswith("-")):
            argument["name"] = args[0] if (len(args) > 0) else argument["dest"]
            self.positionals.append(argument)
            return action

        # Option: argument with one or more flags starting with '-' provided as
        # positional arguments to method
        argument["flags"] = list(args)
        self.options.append(argument)
        return action

    def format_usage(self) -> str:
        # Use user-defined usage message
        if "usage" in self.program:
            prefix = "Usage: "
            wrapper = textwrap.TextWrapper(width=self.width)
            wrapper.initial_indent = prefix
            wrapper.subsequent_indent = len(prefix) * " "
            if self.program["usage"] == "" or str.isspace(self.program["usage"]):
                return wrapper.fill("No usage information available")
            return wrapper.fill(self.program["usage"])

        # Generate usage message from known arguments
        output: list[str] = []

        # Determine what to display left and right, determine string length for left
        # and right
        left1: str = "Usage: "
        left2: str = (
            self.program["prog"]
            if ("prog" in self.program and self.program["prog"] != "" and not str.isspace(self.program["prog"]))
            else os.path.basename(sys.argv[0])
            if (len(sys.argv[0]) > 0 and sys.argv[0] != "" and not str.isspace(sys.argv[0]))
            else "script.py"
        )
        llen: int = len(left1) + len(left2)
        arglist: list[str] = []
        for option in self.options:
            # arglist += [ "[%s]" % item if ("action" in option and (option["action"] == "store_true"
            # or option["action"] == "store_false")) else "[%s %s]" % (item, option["metavar"])
            # if ("metavar" in option) else "[%s %s]" % (item, option["dest"].upper())
            # if ("dest" in option) else "[%s]" % item for item in option["flags"] ]
            flags = str.join("|", option["flags"])
            arglist += [
                f"[{flags}]"
                if ("action" in option and (option["action"] == "store_true" or option["action"] == "store_false"))
                else f"[{flags} {option['metavar']}]"
                if ("metavar" in option)
                else f"[{flags} {option['dest'].upper()}]"
                if ("dest" in option)
                else f"[{flags}]"
            ]
        for positional in self.positionals:
            arglist += [f"{positional['metavar']}" if ("metavar" in positional) else f"{positional['name']}"]
        right: str = str.join(" ", arglist)
        # rlen: int = len(right)

        # Determine width for left and right parts based on string lengths, define
        # output template. Limit width of left part to a maximum of self.width / 2.
        # Use max() to prevent negative values. -1: trailing space (spacing between
        # left and right parts), see template
        lwidth: int = llen
        rwidth: int = max(0, self.width - lwidth - 1)
        if lwidth > int(self.width / 2) - 1:
            lwidth = max(0, int(self.width / 2) - 1)
            rwidth = int(self.width / 2)
        # outtmp = "%-" + str(lwidth) + "s %-" + str(rwidth) + "s"
        outtmp: str = "%-" + str(lwidth) + "s %s"

        # Wrap text for left and right parts, split into separate lines
        wrapper = textwrap.TextWrapper(width=lwidth)
        wrapper.initial_indent = left1
        wrapper.subsequent_indent = len(left1) * " "
        left: list[str] = wrapper.wrap(left2)
        wrapper = textwrap.TextWrapper(width=rwidth)
        right_wrapped: list[str] = wrapper.wrap(right)

        # Add usage message to output
        for i in range(0, max(len(left), len(right_wrapped))):
            left_: str = left[i] if (i < len(left)) else ""
            right_: str = right_wrapped[i] if (i < len(right_wrapped)) else ""
            output.append(outtmp % (left_, right_))

        # Return output as single string
        return str.join("\n", output)

    def format_help(self) -> str:
        output: list[str] = []
        dewrapper: textwrap.TextWrapper = textwrap.TextWrapper(width=self.width)

        # Add usage message to output
        output.append(self.format_usage())

        # Add description to output if present
        if (
            "description" in self.program
            and self.program["description"] != ""
            and not str.isspace(self.program["description"])
        ):
            output.append("")
            output.append(dewrapper.fill(self.program["description"]))

        # Determine what to display left and right for each argument, determine max
        # string lengths for left and right
        lmaxlen: int = 0
        rmaxlen: int = 0
        for positional in self.positionals:
            positional["left"] = positional["metavar"] if ("metavar" in positional) else positional["name"]
        for option in self.options:
            if "action" in option and (option["action"] == "store_true" or option["action"] == "store_false"):
                option["left"] = str.join(", ", option["flags"])
            else:
                option["left"] = str.join(
                    ", ",
                    [
                        f"{item} {option['metavar']}"
                        if ("metavar" in option)
                        else f"{item} {option['dest'].upper()}"
                        if ("dest" in option)
                        else item
                        for item in option["flags"]
                    ],
                )
        for argument in self.positionals + self.options:
            argument["right"] = ""
            if "help" in argument and argument["help"] != "" and not str.isspace(argument["help"]):
                argument["right"] += argument["help"]
            else:
                # argument["right"] += "No description available"
                argument["right"] += "No help available"
            if "choices" in argument and len(argument["choices"]) > 0:
                argument["right"] += " (choices: {})".format(
                    str.join(
                        ", ", (f"'{item}'" if isinstance(item, str) else str(item) for item in argument["choices"])
                    )
                )
            if "default" in argument and argument["default"] != argparse.SUPPRESS:
                # Build the info line with optional pyproject_key
                info_parts = []
                if "pyproject_key" in argument and argument["pyproject_key"]:
                    info_parts.append(f"pyproject: {argument['pyproject_key']}")
                default_value = (
                    f"'{argument['default']}'" if isinstance(argument["default"], str) else str(argument["default"])
                )
                info_parts.append(f"default: {default_value}")
                argument["right"] += "\n({})".format(", ".join(info_parts))
            lmaxlen = max(lmaxlen, len(argument["left"]))
            rmaxlen = max(rmaxlen, len(argument["right"]))

        # Determine width for left and right parts based on maximum string lengths,
        # define output template. Limit width of left part to a maximum of self.width
        # / 2. Use max() to prevent negative values. -4: two leading spaces (indent)
        # + two trailing spaces (spacing between left and right), see template
        lwidth: int = lmaxlen
        rwidth: int = max(0, self.width - lwidth - 4)
        if lwidth > int(self.width / 2) - 4:
            lwidth = max(0, int(self.width / 2) - 4)
            rwidth = int(self.width / 2)
        # outtmp = "  %-" + str(lwidth) + "s  %-" + str(rwidth) + "s"
        outtmp: str = "  %-" + str(lwidth) + "s  %s"

        # Wrap text for left and right parts, split into separate lines
        lwrapper: textwrap.TextWrapper = textwrap.TextWrapper(width=lwidth)
        rwrapper: textwrap.TextWrapper = textwrap.TextWrapper(width=rwidth)
        for argument in self.positionals + self.options:
            argument["left"] = lwrapper.wrap(argument["left"])
            # Handle newlines in right text by splitting first, then wrapping each part
            right_lines: list[str] = []
            for line in argument["right"].split("\n"):
                if line:  # Only wrap non-empty lines
                    right_lines.extend(rwrapper.wrap(line))
                else:
                    right_lines.append("")  # Preserve empty lines
            argument["right"] = right_lines

        # Add positional arguments to output
        if len(self.positionals) > 0:
            output.append("")
            output.append("Positionals:")
            for positional in self.positionals:
                for i in range(0, max(len(positional["left"]), len(positional["right"]))):
                    left: str = positional["left"][i] if (i < len(positional["left"])) else ""
                    right: str = positional["right"][i] if (i < len(positional["right"])) else ""
                    output.append(outtmp % (left, right))

        # Add option arguments to output
        if len(self.options) > 0:
            output.append("")
            output.append("Options:")
            for option in self.options:
                for i in range(0, max(len(option["left"]), len(option["right"]))):
                    left = option["left"][i] if (i < len(option["left"])) else ""
                    right = option["right"][i] if (i < len(option["right"])) else ""
                    output.append(outtmp % (left, right))

        # Add epilog to output if present
        if "epilog" in self.program and self.program["epilog"] != "" and not str.isspace(self.program["epilog"]):
            output.append("")
            # Handle newlines in epilog by splitting first, then wrapping each part
            for line in self.program["epilog"].split("\n"):
                if line:  # Only wrap non-empty lines
                    output.append(dewrapper.fill(line))
                else:
                    output.append("")  # Preserve empty lines

        # Return output as single string
        return str.join("\n", output)

    # Method redefined as format_usage() does not return a trailing newline like
    # the original does
    def print_usage(self, file: SupportsWrite[str] | None = None) -> None:
        if file is None:
            file = sys.stdout
        file.write(self.format_usage() + "\n")
        file.flush()

    # Method redefined as format_help() does not return a trailing newline like
    # the original does
    def print_help(self, file: SupportsWrite[str] | None = None) -> None:
        if file is None:
            file = sys.stdout
        file.write(self.format_help() + "\n")
        file.flush()

    def error(self, message: str) -> Never:
        sys.stderr.write(self.format_usage() + "\n")
        sys.stderr.write((f"Error: {message}") + "\n")
        sys.exit(2)


# -------------------------------------
#                                     -
#  Demo                               -
#                                     -
# -------------------------------------

# Demonstrate module usage and features if run directly
if __name__ == "__main__":
    # Create CustomArgumentParser
    parser = CustomArgumentParser(
        description="Description message displayed after usage and before positional arguments and options.\n"
        "Can be used to describe the application in a short summary. Optional, omitted if empty.",
        epilog="Epilog message displayed at the bottom after everything else. "
        "Can be used to provide additional information, e.g. license, contact details, copyright etc. Optional, "
        "omitted if empty.",
        argument_default=argparse.SUPPRESS,
        allow_abbrev=False,
        add_help=False,
    )

    # Add options
    parser.add_argument(
        "-c", "--config-file", action="store", dest="config_file", metavar="FILE", type=str, default="config.ini"
    )
    parser.add_argument(
        "-d",
        "--database-file",
        action="store",
        dest="database_file",
        metavar="file",
        type=str,
        help="SQLite3 database file to read/write",
        default="database.db",
        pyproject_key="tool.myapp.database.file",
    )
    parser.add_argument(
        "-l",
        "--log-file",
        action="store",
        dest="log_file",
        metavar="file",
        type=str,
        help="File to write log to",
        default="debug.log",
    )
    parser.add_argument(
        "-t", "--threads", action="store", dest="threads", type=int, help="Number of threads to spawn", default=3
    )
    parser.add_argument(
        "-p",
        "--port",
        action="store",
        dest="port",
        type=int,
        help="TCP port to listen on for access to the web interface",
        choices=[80, 8080, 8081],
        default=8080,
    )
    parser.add_argument(
        "--max-downloads",
        action="store",
        dest="max_downloads",
        metavar="value",
        type=int,
        help="Maximum number of concurrent downloads",
        default=5,
    )
    parser.add_argument(
        "--download-timeout",
        action="store",
        dest="download_timeout",
        metavar="value",
        type=int,
        help="Download timeout in seconds",
        default=120,
    )
    parser.add_argument(
        "--max-requests",
        action="store",
        dest="max_requests",
        metavar="value",
        type=int,
        help="Maximum number of concurrent requests",
        default=10,
    )
    parser.add_argument(
        "--request-timeout",
        action="store",
        dest="request_timeout",
        metavar="value",
        type=int,
        help="Request timeout in seconds",
        default=60,
    )
    parser.add_argument(
        "--output-facility",
        action="store",
        dest="output_facility",
        metavar="value",
        type=str.lower,
        choices=["stdout", "stderr"],
        help="Output facility to use for console output",
        default="stdout",
    )
    parser.add_argument(
        "--log-level",
        action="store",
        dest="log_level",
        metavar="VALUE",
        type=str.lower,
        choices=["debug", "info", "warning", "error", "critical"],
        help="Log level to use",
        default="info",
    )
    parser.add_argument(
        "--use-color",
        action="store",
        dest="use_color",
        metavar="value",
        type=bool,
        help="Colorize console output",
        default=True,
    )
    parser.add_argument("--log-template", action="store", dest="log_template", metavar="value", type=str)
    parser.add_argument(
        "-s",
        "--some-option",
        action="store",
        dest="some_option",
        metavar="VALUE",
        type=str,
        help="Some fancy option with miscellaneous choices",
        choices=[123, "foobar", False],
    )
    parser.add_argument("-h", "--help", action="help", help="Display this message")

    # Add positionals
    parser.add_argument("input_url", action="store", metavar="URL", type=str, help="URL to download from")
    parser.add_argument("output_file", action="store", metavar="DEST", type=str, help="File to save download as")

    # Parse command line
    args = parser.parse_args()
    print("Command line parsed successfully.")
