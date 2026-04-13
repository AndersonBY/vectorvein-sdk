"""Authentication and user parser builders."""

from __future__ import annotations

import argparse

from vectorvein.cli._builders.common import rich_parser_kwargs
from vectorvein.cli._commands.auth import _cmd_auth_whoami, _cmd_user_info, _cmd_user_validate_api_key


def register_auth_parsers(top_level: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    auth_parser = top_level.add_parser(
        "auth",
        help="Authentication related commands.",
        **rich_parser_kwargs(
            "Inspect the current API identity and confirm which account the CLI is using.",
            examples=[
                "vectorvein auth whoami",
                "vectorvein --format json auth whoami",
            ],
        ),
    )
    auth_sub = auth_parser.add_subparsers(dest="auth_command")
    auth_sub.required = True

    auth_whoami = auth_sub.add_parser(
        "whoami",
        help="Show current account profile summary.",
        **rich_parser_kwargs(
            "Return the current account summary, including uid, username, email, credits, and join time.",
            examples=["vectorvein auth whoami"],
        ),
    )
    auth_whoami.set_defaults(handler=_cmd_auth_whoami, command="auth whoami")

    user_parser = top_level.add_parser(
        "user",
        help="User profile commands.",
        **rich_parser_kwargs(
            "Inspect the current user profile and validate API credentials.",
            examples=[
                "vectorvein user info",
                "vectorvein user validate-api-key",
            ],
        ),
    )
    user_sub = user_parser.add_subparsers(dest="user_command")
    user_sub.required = True

    user_info = user_sub.add_parser(
        "info",
        help="Fetch current user profile (user-info/get).",
        **rich_parser_kwargs("Fetch the full current user profile from the Open API.", examples=["vectorvein user info"]),
    )
    user_info.set_defaults(handler=_cmd_user_info, command="user info")

    user_validate = user_sub.add_parser(
        "validate-api-key",
        help="Validate API key (user/validate-api-key).",
        **rich_parser_kwargs("Validate the currently provided API key and return the resolved user identity.", examples=["vectorvein user validate-api-key"]),
    )
    user_validate.set_defaults(handler=_cmd_user_validate_api_key, command="user validate-api-key")
