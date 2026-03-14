"""API request command handler."""

from __future__ import annotations

import argparse
from typing import Any

from vectorvein.api import VectorVeinClient

from vectorvein.cli._output import CLIUsageError
from vectorvein.cli._parsers import _load_json_object


def _cmd_api_request(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    params = _load_json_object(args.params, "--params") if args.params else None
    body: dict[str, Any] | None = None
    if args.body:
        body = _load_json_object(args.body, "--body")

    endpoint = str(args.endpoint).strip("/")
    if not endpoint:
        raise CLIUsageError("--endpoint cannot be empty")

    return client._request(
        method=args.method,
        endpoint=endpoint,
        params=params,
        json=body,
        api_key_type=args.api_key_type,
    )
