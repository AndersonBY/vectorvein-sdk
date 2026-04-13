"""CLI output formatting and error/success payload builders."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from typing import Any, NoReturn


def _repair_usage_message(message: str, prog: str) -> tuple[str, str | None, list[str], str | None, str | None]:
    normalized_prog = prog.strip()

    if normalized_prog.endswith("task-agent") and "argument task_agent_group: invalid choice:" in message:
        return (
            "task-agent requires a subgroup before an action.",
            "Choose a subgroup such as agent, task, cycle, skill, or collection before the action name.",
            [
                "vectorvein task-agent agent create --name 'My Agent'",
                "vectorvein task-agent task create --agent-id agent_xxx --text 'Do work'",
                "vectorvein task-agent -h",
            ],
            "vectorvein task-agent <group> <action> [options]",
            "vectorvein task-agent agent create --name 'Research Assistant'",
        )

    if normalized_prog.endswith("task-agent agent") and "the following arguments are required: task_agent_agent_command" in message:
        return (
            "task-agent agent requires an action.",
            "Pick an action such as list, get, create, update, duplicate, or toggle-favorite.",
            [
                "vectorvein task-agent agent list",
                "vectorvein task-agent agent create --name 'My Agent'",
                "vectorvein task-agent agent -h",
            ],
            "vectorvein task-agent agent <action> [options]",
            "vectorvein task-agent agent create --name 'Research Assistant'",
        )

    if normalized_prog.endswith("task-agent task") and "the following arguments are required: task_agent_task_command" in message:
        return (
            "task-agent task requires an action.",
            "Pick an action such as list, get, create, continue, respond, or update-share.",
            [
                "vectorvein task-agent task list",
                "vectorvein task-agent task create --agent-id agent_xxx --text 'Summarize this report'",
                "vectorvein task-agent task -h",
            ],
            "vectorvein task-agent task <action> [options]",
            "vectorvein task-agent task create --agent-id agent_xxx --text 'Summarize this report'",
        )

    return message, None, [], None, None


class CLIUsageError(ValueError):
    """Raised when CLI usage or argument values are invalid."""

    def __init__(
        self,
        message: str,
        *,
        hint: str | None = None,
        suggestions: list[str] | None = None,
        expected_command: str | None = None,
        example: str | None = None,
    ):
        super().__init__(message)
        self.hint = hint
        self.suggestions = list(suggestions or [])
        self.expected_command = expected_command
        self.example = example


class CLIArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that raises usage errors instead of exiting."""

    def error(self, message: str) -> NoReturn:  # noqa: D401
        repaired_message, hint, suggestions, expected_command, example = _repair_usage_message(message, self.prog)
        raise CLIUsageError(
            repaired_message,
            hint=hint,
            suggestions=suggestions,
            expected_command=expected_command,
            example=example,
        )


def _normalize(value: Any) -> Any:
    """Convert SDK models/dataclasses into plain JSON-serializable data."""
    if is_dataclass(value):
        return _normalize(asdict(value))
    if isinstance(value, dict):
        return {str(key): _normalize(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize(item) for item in value]
    return value


def _print_json(payload: dict[str, Any], *, compact: bool, stream: Any | None = None) -> None:
    target_stream = sys.stdout if stream is None else stream
    indent = None if compact else 2
    json_text = json.dumps(payload, ensure_ascii=False, indent=indent)
    target_stream.write(f"{json_text}\n")


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, str | int | float | bool)


def _format_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _render_text_lines(value: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent
    if _is_scalar(value):
        return [f"{prefix}{_format_scalar(value)}"]

    if isinstance(value, dict):
        if not value:
            return [f"{prefix}{{}}"]
        lines: list[str] = []
        for key, child in value.items():
            key_text = str(key)
            if _is_scalar(child):
                lines.append(f"{prefix}{key_text}: {_format_scalar(child)}")
            else:
                lines.append(f"{prefix}{key_text}:")
                lines.extend(_render_text_lines(child, indent + 2))
        return lines

    if isinstance(value, list):
        if not value:
            return [f"{prefix}[]"]
        lines = []
        for item in value:
            if _is_scalar(item):
                lines.append(f"{prefix}- {_format_scalar(item)}")
            else:
                lines.append(f"{prefix}-")
                lines.extend(_render_text_lines(item, indent + 2))
        return lines

    return [f"{prefix}{value}"]


def _print_text_success(data: Any, stream: Any | None = None) -> None:
    target_stream = sys.stdout if stream is None else stream
    normalized = _normalize(data)
    lines = _render_text_lines(normalized)
    target_stream.write("\n".join(lines))
    target_stream.write("\n")


def _print_text_error(payload: dict[str, Any], stream: Any | None = None) -> None:
    target_stream = sys.stderr if stream is None else stream
    error = payload.get("error", {})
    command = payload.get("command")
    error_type = str(error.get("type", "error"))
    message = str(error.get("message", "Unknown error"))
    status_code = error.get("status_code")
    hint = error.get("hint")
    suggestions = error.get("suggestions") or []
    expected_command = error.get("expected_command")
    example = error.get("example")
    details = error.get("details")

    if command:
        target_stream.write(f"Error [{error_type}] ({command}): {message}\n")
    else:
        target_stream.write(f"Error [{error_type}]: {message}\n")

    if status_code is not None:
        target_stream.write(f"Status Code: {status_code}\n")
    if hint:
        target_stream.write(f"Hint: {hint}\n")
    if expected_command:
        target_stream.write(f"Expected Command: {expected_command}\n")
    if suggestions:
        target_stream.write("Suggestions:\n")
        for suggestion in suggestions:
            target_stream.write(f"  - {suggestion}\n")
    if example:
        target_stream.write(f"Example: {example}\n")
    if isinstance(details, dict) and "traceback" in details:
        target_stream.write("\nTraceback:\n")
        target_stream.write(f"{details['traceback']}\n")


def _success_payload(command: str, data: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "command": command,
        "data": _normalize(data),
    }


def _error_payload(
    command: str | None,
    error_type: str,
    message: str,
    *,
    hint: str | None = None,
    suggestions: list[str] | None = None,
    expected_command: str | None = None,
    example: str | None = None,
    status_code: int | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {"type": error_type, "message": message}
    if status_code is not None:
        error["status_code"] = status_code
    if hint:
        error["hint"] = hint
    if suggestions:
        error["suggestions"] = suggestions
    if expected_command:
        error["expected_command"] = expected_command
    if example:
        error["example"] = example
    if details:
        error["details"] = details

    payload: dict[str, Any] = {"ok": False, "error": error}
    if command:
        payload["command"] = command
    return payload
