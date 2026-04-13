"""CLI argument parsing utility functions."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

from vectorvein.api import (
    AgentDefinition,
    AgentSettings,
    AttachmentDetail,
    OssAttachmentDetail,
    VectorVeinClient,
    WorkflowInputField,
)

from vectorvein.cli._output import CLIUsageError

ENV_API_KEY = "VECTORVEIN_API_KEY"
ENV_BASE_URL = "VECTORVEIN_BASE_URL"
_AGENT_DEFINITION_EXAMPLE = '{"model_name":"gpt-4o","backend_type":"openai","compress_memory_after_tokens":64000}'
_AGENT_SETTINGS_EXAMPLE = '{"model_name":"gpt-4o","backend_type":"openai","compress_memory_after_tokens":64000}'
TEXT_AT_FILE_OPTIONS = {
    "--description",
    "--brief",
    "--comment",
    "--optimization-direction",
    "--system-prompt",
    "--default-output-verifier",
    "--text",
    "--message",
    "--response",
    "--content",
}


def _parse_bool_text(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y", "on"}:
        return True
    if normalized in {"false", "0", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError("expected a boolean value: true or false")


def _load_json_value(raw: str, option_name: str) -> Any:
    source = option_name
    text = raw
    if raw.startswith("@"):
        path = Path(raw[1:])
        if not path.exists():
            raise CLIUsageError(f"{option_name} references missing file: {path}")
        if not path.is_file():
            raise CLIUsageError(f"{option_name} expects a file path after '@': {path}")
        text = path.read_text(encoding="utf-8")
        source = f"{option_name} ({path})"

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise CLIUsageError(f"{source} contains invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc


def _load_text_value(raw: str, option_name: str) -> str:
    if raw.startswith("@"):
        path = Path(raw[1:])
        if not path.exists():
            raise CLIUsageError(f"{option_name} references missing file: {path}")
        if not path.is_file():
            raise CLIUsageError(f"{option_name} expects a file path after '@': {path}")
        return path.read_text(encoding="utf-8")
    return raw


def _load_json_object(raw: str, option_name: str) -> dict[str, Any]:
    value = _load_json_value(raw, option_name)
    if not isinstance(value, dict):
        raise CLIUsageError(f"{option_name} must be a JSON object")
    return value


def _load_json_array(raw: str, option_name: str) -> list[Any]:
    value = _load_json_value(raw, option_name)
    if not isinstance(value, list):
        raise CLIUsageError(f"{option_name} must be a JSON array")
    return value


def _load_optional_json_object(raw: str | None, option_name: str) -> dict[str, Any] | None:
    if not raw:
        return None
    return _load_json_object(raw, option_name)


def _load_optional_json_array(raw: str | None, option_name: str) -> list[Any] | None:
    if not raw:
        return None
    return _load_json_array(raw, option_name)


def _load_optional_text_value(raw: str | None, option_name: str) -> str | None:
    if raw is None:
        return None
    return _load_text_value(raw, option_name)


def _require_api_key(args: argparse.Namespace) -> str:
    if args.api_key:
        return str(args.api_key)

    env_api_key = os.getenv(ENV_API_KEY, "").strip()
    if env_api_key:
        return env_api_key

    raise CLIUsageError(f"Missing API key. Use --api-key or set environment variable {ENV_API_KEY}.")


def _resolve_base_url(args: argparse.Namespace) -> str | None:
    if args.base_url:
        return str(args.base_url)
    env_base_url = os.getenv(ENV_BASE_URL, "").strip()
    return env_base_url or None


def _parse_workflow_input_field(value: Any, source: str) -> WorkflowInputField:
    if not isinstance(value, dict):
        raise CLIUsageError(f"{source} must be a JSON object with keys: node_id, field_name, value")

    missing = [key for key in ("node_id", "field_name", "value") if key not in value]
    if missing:
        raise CLIUsageError(f"{source} is missing required key(s): {', '.join(missing)}")

    return WorkflowInputField(
        node_id=str(value["node_id"]),
        field_name=str(value["field_name"]),
        value=value["value"],
    )


def _collect_workflow_input_fields(args: argparse.Namespace) -> list[WorkflowInputField]:
    raw_items: list[Any] = []

    if args.input_fields:
        raw_items.extend(_load_json_array(args.input_fields, "--input-fields"))

    for index, raw in enumerate(args.input_field or [], start=1):
        raw_items.append(_load_json_value(raw, f"--input-field[{index}]"))

    if not raw_items:
        raise CLIUsageError("No workflow input fields provided. Use --input-field or --input-fields.")

    return [_parse_workflow_input_field(item, f"input_fields[{idx}]") for idx, item in enumerate(raw_items)]


def _collect_optional_workflow_input_fields(args: argparse.Namespace) -> list[WorkflowInputField]:
    raw_items: list[Any] = []

    if args.input_fields:
        raw_items.extend(_load_json_array(args.input_fields, "--input-fields"))

    for index, raw in enumerate(args.input_field or [], start=1):
        raw_items.append(_load_json_value(raw, f"--input-field[{index}]"))

    return [_parse_workflow_input_field(item, f"input_fields[{idx}]") for idx, item in enumerate(raw_items)]


def _parse_upload_to_spec(spec: str, source: str) -> tuple[str, str, Path]:
    parts = spec.split(":", 2)
    if len(parts) != 3:
        raise CLIUsageError(f"{source} must be 'node_id:field_name:local_file_path'.")

    node_id = parts[0].strip()
    field_name = parts[1].strip()
    path_text = parts[2].strip()
    if not node_id:
        raise CLIUsageError(f"{source} is missing node_id.")
    if not field_name:
        raise CLIUsageError(f"{source} is missing field_name.")
    if not path_text:
        raise CLIUsageError(f"{source} is missing local_file_path.")

    local_path = Path(path_text)
    if not local_path.exists():
        raise CLIUsageError(f"{source} file does not exist: {local_path}")
    if not local_path.is_file():
        raise CLIUsageError(f"{source} path must point to a file: {local_path}")
    return node_id, field_name, local_path


def _collect_uploaded_workflow_input_fields(args: argparse.Namespace, client: VectorVeinClient) -> list[WorkflowInputField]:
    upload_specs = list(args.upload_to or [])
    if not upload_specs:
        return []

    grouped_paths: dict[tuple[str, str], list[Path]] = {}
    for index, spec in enumerate(upload_specs, start=1):
        node_id, field_name, local_path = _parse_upload_to_spec(spec, f"--upload-to[{index}]")
        grouped_paths.setdefault((node_id, field_name), []).append(local_path)

    uploaded_input_fields: list[WorkflowInputField] = []
    for (node_id, field_name), paths in grouped_paths.items():
        uploaded_paths: list[str] = []
        for local_path in paths:
            upload_result = client.upload_file(str(local_path))
            uploaded_paths.append(upload_result.oss_path)

        upload_as = str(args.upload_as)
        if upload_as == "single":
            if len(uploaded_paths) != 1:
                raise CLIUsageError(f"Field {node_id}:{field_name} received {len(uploaded_paths)} files, but --upload-as single requires exactly one file.")
            value: Any = uploaded_paths[0]
        elif upload_as == "list":
            value = uploaded_paths
        else:
            value = uploaded_paths[0] if len(uploaded_paths) == 1 else uploaded_paths

        uploaded_input_fields.append(WorkflowInputField(node_id=node_id, field_name=field_name, value=value))

    return uploaded_input_fields


def _parse_attachment_item(value: Any, source: str) -> AttachmentDetail | OssAttachmentDetail:
    if not isinstance(value, dict):
        raise CLIUsageError(f"{source} must be a JSON object")

    name = value.get("name")
    if not isinstance(name, str) or not name.strip():
        raise CLIUsageError(f"{source}.name must be a non-empty string")

    has_url = "url" in value and value.get("url") is not None
    has_oss_key = "oss_key" in value and value.get("oss_key") is not None
    if has_url == has_oss_key:
        raise CLIUsageError(f"{source} must contain exactly one of 'url' or 'oss_key'")

    if has_url:
        return AttachmentDetail(name=name, url=str(value["url"]))
    return OssAttachmentDetail(name=name, oss_key=str(value["oss_key"]))


def _collect_attachments(args: argparse.Namespace) -> list[AttachmentDetail | OssAttachmentDetail] | None:
    raw_items: list[Any] = []
    if getattr(args, "attachments", None):
        raw_items.extend(_load_json_array(args.attachments, "--attachments"))

    for index, raw in enumerate(getattr(args, "attachment", []) or [], start=1):
        raw_items.append(_load_json_value(raw, f"--attachment[{index}]"))

    if not raw_items:
        return None

    return [_parse_attachment_item(item, f"attachments[{idx}]") for idx, item in enumerate(raw_items)]


def _collect_url_attachments(args: argparse.Namespace) -> list[AttachmentDetail] | None:
    attachments = _collect_attachments(args)
    if not attachments:
        return None

    url_attachments: list[AttachmentDetail] = []
    for idx, attachment in enumerate(attachments):
        if isinstance(attachment, AttachmentDetail):
            url_attachments.append(attachment)
            continue
        raise CLIUsageError(f"attachments[{idx}] uses 'oss_key', but this command only accepts URL attachments.")
    return url_attachments


def _load_optional_agent_definition(raw: str | None) -> AgentDefinition | None:
    if not raw:
        return None
    payload = _load_json_object(raw, "--agent-definition")
    if "compress_memory_after_characters" in payload:
        raise CLIUsageError(
            "--agent-definition does not match AgentDefinition schema: compress_memory_after_characters is no longer supported.",
            hint="Use the token-based memory threshold field instead.",
            suggestions=["Rename compress_memory_after_characters -> compress_memory_after_tokens."],
            example=_AGENT_DEFINITION_EXAMPLE,
        )
    try:
        return AgentDefinition(**payload)
    except TypeError as exc:
        raise CLIUsageError(
            f"--agent-definition does not match AgentDefinition schema: {exc}",
            hint="Use the latest AgentDefinition fields and JSON object shape.",
            example=_AGENT_DEFINITION_EXAMPLE,
        ) from exc


def _load_optional_agent_settings(raw: str | None) -> AgentSettings | None:
    if not raw:
        return None
    payload = _load_json_object(raw, "--agent-settings")
    if "compress_memory_after_characters" in payload:
        raise CLIUsageError(
            "--agent-settings does not match AgentSettings schema: compress_memory_after_characters is no longer supported.",
            hint="Use the token-based memory threshold field instead.",
            suggestions=["Rename compress_memory_after_characters -> compress_memory_after_tokens."],
            example=_AGENT_SETTINGS_EXAMPLE,
        )
    try:
        return AgentSettings(**payload)
    except TypeError as exc:
        raise CLIUsageError(
            f"--agent-settings does not match AgentSettings schema: {exc}",
            hint="Use the latest AgentSettings fields and JSON object shape.",
            example=_AGENT_SETTINGS_EXAMPLE,
        ) from exc


_TASK_TERMINAL_STATUSES = {"completed", "failed", "error"}


def _poll_task_until_done(
    client: VectorVeinClient,
    task_id: str,
    timeout: int,
) -> Any:
    """Poll task status until terminal, waiting, or timeout."""
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            return {"task_id": task_id, "status": "timeout", "timeout": timeout}
        task = client.get_agent_task(task_id=task_id)
        if task.status in _TASK_TERMINAL_STATUSES:
            return task
        if task.status == "waiting" and task.waiting_question:
            return task
        time.sleep(3)
