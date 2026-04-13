"""Raw API parser builder."""

from __future__ import annotations

import argparse

from vectorvein.cli._builders.common import rich_parser_kwargs
from vectorvein.cli._commands.api import _cmd_api_request


def register_api_parser(top_level: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    api_parser = top_level.add_parser(
        "api",
        help="Low-level API request command for unsupported operations.",
        **rich_parser_kwargs(
            "Send raw Open API requests when a high-level CLI command is not available yet.",
            examples=[
                "vectorvein api request --method GET --endpoint user-info/get",
                'vectorvein api request --method POST --endpoint workflow/list --body \'{"page":1,"page_size":10}\'',
                "vectorvein api request --method POST --endpoint workflow/check-status --body @payload.json",
            ],
            notes=[
                "--params and --body accept inline JSON or @file paths.",
                "Use this command as a fallback when you need an endpoint that has not been promoted into a dedicated CLI command yet.",
            ],
        ),
    )
    api_sub = api_parser.add_subparsers(dest="api_command")
    api_sub.required = True

    api_request = api_sub.add_parser(
        "request",
        help="Send a raw request to Open API endpoint.",
        **rich_parser_kwargs(
            "Send a raw Open API request. Prefer dedicated commands when available because they validate arguments for you.",
            examples=[
                'vectorvein api request --method POST --endpoint workflow/list --body \'{"page":1,"page_size":10}\'',
                "vectorvein api request --method GET --endpoint user-info/get",
                "vectorvein api request --method POST --endpoint workflow/check-status --body @payload.json",
            ],
            notes=[
                "--params and --body must be JSON objects.",
                "@file syntax reads request data from a UTF-8 JSON file.",
            ],
        ),
    )
    api_request.add_argument("--method", choices=("GET", "POST", "PUT", "PATCH", "DELETE"), default="POST", help="HTTP method (default: POST).")
    api_request.add_argument("--endpoint", required=True, help="Open API endpoint path, for example workflow/list.")
    api_request.add_argument("--params", help="JSON object or @file for query parameters.")
    api_request.add_argument("--body", help="JSON object or @file for request body.")
    api_request.add_argument("--api-key-type", choices=("WORKFLOW", "VAPP"), default="WORKFLOW", help="API key type header (default: WORKFLOW).")
    api_request.set_defaults(handler=_cmd_api_request, command="api request")
