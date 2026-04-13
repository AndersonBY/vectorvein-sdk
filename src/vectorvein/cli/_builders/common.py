"""Shared CLI builder helpers."""

from __future__ import annotations

import argparse
from textwrap import dedent

from vectorvein.cli._parsers import _parse_bool_text


def _format_default_value(value: bool | str) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


class RichHelpFormatter(argparse.RawTextHelpFormatter):
    """Help formatter with raw newlines for curated examples and notes."""

    def _get_help_string(self, action: argparse.Action) -> str | None:
        help_text = action.help
        if help_text is argparse.SUPPRESS:
            return help_text
        if not isinstance(help_text, str):
            return help_text

        display_default = getattr(action, "display_default", None)
        if display_default is None and isinstance(action.default, bool):
            display_default = _format_default_value(action.default)

        if display_default is not None and "default:" not in help_text.lower():
            return f"{help_text} Default: {display_default}."
        return help_text


def _section(title: str, lines: list[str]) -> str:
    if not lines:
        return ""
    return f"{title}:\n" + "\n".join(f"  {line}" for line in lines)


def rich_parser_kwargs(
    description: str,
    *,
    examples: list[str] | None = None,
    notes: list[str] | None = None,
    fixes: list[str] | None = None,
) -> dict[str, object]:
    sections = [section for section in [_section("Examples", examples or []), _section("JSON and @file Inputs", notes or []), _section("Common Fixes", fixes or [])] if section]
    return {
        "description": dedent(description).strip(),
        "epilog": "\n\n".join(sections) if sections else None,
        "formatter_class": RichHelpFormatter,
    }


def add_paging_arguments(parser: argparse.ArgumentParser, *, default_page: int = 1, default_page_size: int = 10) -> None:
    parser.add_argument("--page", type=int, default=default_page, help=f"Page number (default: {default_page}).")
    parser.add_argument("--page-size", type=int, default=default_page_size, help=f"Page size (default: {default_page_size}).")


def add_search_argument(parser: argparse.ArgumentParser, *, option: str = "--search", help_text: str = "Search keyword.") -> None:
    parser.add_argument(option, help=help_text)


def add_json_data_argument(parser: argparse.ArgumentParser, *, help_text: str = "Additional JSON object or @file merged into the request payload.") -> None:
    parser.add_argument("--data", help=help_text)


def add_bool_text_argument(
    parser: argparse.ArgumentParser,
    option: str,
    *,
    help_text: str,
    dest: str | None = None,
    display_default: bool | str = "not set",
) -> None:
    action = parser.add_argument(option, dest=dest, type=_parse_bool_text, metavar="BOOL", help=f"{help_text} Accepted values: true or false.")
    action.display_default = _format_default_value(display_default)
