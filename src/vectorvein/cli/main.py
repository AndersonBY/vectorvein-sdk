"""VectorVein CLI entrypoint."""

from __future__ import annotations

import sys
import time  # noqa: F401 — kept for monkeypatch compatibility
import traceback
from collections.abc import Sequence
from typing import Any

from vectorvein.api import (
    APIKeyError,
    RequestError,
    VectorVeinAPIError,
    VectorVeinClient,
)

from vectorvein.cli._output import (
    CLIUsageError,
    _error_payload,
    _print_json,
    _print_text_error,
    _print_text_success,
    _success_payload,
)
from vectorvein.cli._parsers import (
    ENV_API_KEY,
    _require_api_key,
    _resolve_base_url,
)
from vectorvein.cli._parser_builder import build_parser

EXIT_OK = 0
EXIT_UNEXPECTED = 1
EXIT_USAGE = 2
EXIT_AUTH = 3
EXIT_API = 4
EXIT_REQUEST = 5

GLOBAL_FLAG_OPTIONS = {"--compact", "--debug", "--version"}
GLOBAL_VALUE_OPTIONS = {"--api-key", "--base-url", "--format"}


def _normalize_global_options(argv: Sequence[str] | None) -> list[str] | None:
    if argv is None:
        return None

    moved: list[str] = []
    remaining: list[str] = []
    args = list(argv)

    index = 0
    while index < len(args):
        token = args[index]

        if token in GLOBAL_FLAG_OPTIONS:
            moved.append(token)
            index += 1
            continue

        if token in GLOBAL_VALUE_OPTIONS:
            moved.append(token)
            if index + 1 < len(args):
                moved.append(args[index + 1])
                index += 2
            else:
                index += 1
            continue

        if any(token.startswith(f"{option}=") for option in GLOBAL_VALUE_OPTIONS | {"--version"}):
            moved.append(token)
            index += 1
            continue

        remaining.append(token)
        index += 1

    return moved + remaining


def _is_json_output_requested(raw_args: Sequence[str]) -> bool:
    args = list(raw_args)
    for index, token in enumerate(args):
        if token == "--format" and index + 1 < len(args):
            return args[index + 1] == "json"
        if token.startswith("--format="):
            return token.split("=", 1)[1] == "json"
    return False


def _run_with_client(args: Any) -> dict[str, Any]:
    if not hasattr(args, "handler"):
        raise CLIUsageError("No command specified. Run `vectorvein --help` for usage.")

    api_key = _require_api_key(args)
    base_url = _resolve_base_url(args)
    with VectorVeinClient(api_key=api_key, base_url=base_url) as client:
        result = args.handler(args, client)
    return _success_payload(str(args.command), result)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    compact_output = False
    json_output = False
    command: str | None = None
    debug = False

    try:
        raw_args = list(argv) if argv is not None else sys.argv[1:]
        json_output = _is_json_output_requested(raw_args)
        if not raw_args:
            parser.print_help()
            return EXIT_OK
        args = parser.parse_args(_normalize_global_options(raw_args))
        compact_output = bool(getattr(args, "compact", False))
        json_output = str(getattr(args, "format", "text")) == "json"
        command = str(getattr(args, "command", "")) or None
        debug = bool(getattr(args, "debug", False))
        payload = _run_with_client(args)
        if json_output:
            _print_json(payload, compact=compact_output)
        else:
            _print_text_success(payload.get("data"))
        return EXIT_OK
    except CLIUsageError as exc:
        details = {"traceback": traceback.format_exc()} if debug else None
        payload = _error_payload(
            command=command,
            error_type="usage_error",
            message=str(exc),
            hint="Run `vectorvein --help` or `<command> --help` to inspect required arguments.",
            details=details,
        )
        if json_output:
            _print_json(payload, compact=compact_output, stream=sys.stderr)
        else:
            _print_text_error(payload, stream=sys.stderr)
        return EXIT_USAGE
    except APIKeyError as exc:
        details = {"traceback": traceback.format_exc()} if debug else None
        payload = _error_payload(
            command=command,
            error_type="api_key_error",
            message=str(exc),
            hint=f"Check --api-key or {ENV_API_KEY}.",
            status_code=exc.status_code,
            details=details,
        )
        if json_output:
            _print_json(payload, compact=compact_output, stream=sys.stderr)
        else:
            _print_text_error(payload, stream=sys.stderr)
        return EXIT_AUTH
    except RequestError as exc:
        details = {"traceback": traceback.format_exc()} if debug else None
        payload = _error_payload(
            command=command,
            error_type="request_error",
            message=str(exc),
            hint="Check network connectivity and --base-url.",
            details=details,
        )
        if json_output:
            _print_json(payload, compact=compact_output, stream=sys.stderr)
        else:
            _print_text_error(payload, stream=sys.stderr)
        return EXIT_REQUEST
    except VectorVeinAPIError as exc:
        details = {"traceback": traceback.format_exc()} if debug else None
        payload = _error_payload(
            command=command,
            error_type="api_error",
            message=str(exc),
            status_code=exc.status_code,
            details=details,
        )
        if json_output:
            _print_json(payload, compact=compact_output, stream=sys.stderr)
        else:
            _print_text_error(payload, stream=sys.stderr)
        return EXIT_API
    except Exception as exc:  # noqa: BLE001
        details = {"traceback": traceback.format_exc()} if debug else None
        payload = _error_payload(
            command=command,
            error_type="unexpected_error",
            message=str(exc),
            details=details,
        )
        if json_output:
            _print_json(payload, compact=compact_output, stream=sys.stderr)
        else:
            _print_text_error(payload, stream=sys.stderr)
        return EXIT_UNEXPECTED


if __name__ == "__main__":
    raise SystemExit(main())
