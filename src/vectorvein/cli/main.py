"""VectorVein CLI entrypoint."""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from collections.abc import Sequence
from dataclasses import asdict, is_dataclass
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
from typing import Any, NoReturn

from vectorvein.api import (
    APIKeyError,
    AgentDefinition,
    AgentSettings,
    AttachmentDetail,
    OssAttachmentDetail,
    RequestError,
    TaskInfo,
    VectorVeinAPIError,
    VectorVeinClient,
    WorkflowInputField,
)

EXIT_OK = 0
EXIT_UNEXPECTED = 1
EXIT_USAGE = 2
EXIT_AUTH = 3
EXIT_API = 4
EXIT_REQUEST = 5

ENV_API_KEY = "VECTORVEIN_API_KEY"
ENV_BASE_URL = "VECTORVEIN_BASE_URL"
GLOBAL_FLAG_OPTIONS = {"--compact", "--debug", "--version"}
GLOBAL_VALUE_OPTIONS = {"--api-key", "--base-url", "--format"}


class CLIUsageError(ValueError):
    """Raised when CLI usage or argument values are invalid."""


class CLIArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that raises usage errors instead of exiting."""

    def error(self, message: str) -> NoReturn:  # noqa: D401
        raise CLIUsageError(message)


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
    details = error.get("details")

    if command:
        target_stream.write(f"Error [{error_type}] ({command}): {message}\n")
    else:
        target_stream.write(f"Error [{error_type}]: {message}\n")

    if status_code is not None:
        target_stream.write(f"Status Code: {status_code}\n")
    if hint:
        target_stream.write(f"Hint: {hint}\n")
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
    status_code: int | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {"type": error_type, "message": message}
    if status_code is not None:
        error["status_code"] = status_code
    if hint:
        error["hint"] = hint
    if details:
        error["details"] = details

    payload: dict[str, Any] = {"ok": False, "error": error}
    if command:
        payload["command"] = command
    return payload


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
    try:
        return AgentDefinition(**payload)
    except TypeError as exc:
        raise CLIUsageError(f"--agent-definition does not match AgentDefinition schema: {exc}") from exc


def _load_optional_agent_settings(raw: str | None) -> AgentSettings | None:
    if not raw:
        return None
    payload = _load_json_object(raw, "--agent-settings")
    try:
        return AgentSettings(**payload)
    except TypeError as exc:
        raise CLIUsageError(f"--agent-settings does not match AgentSettings schema: {exc}") from exc


def _cmd_auth_whoami(args: argparse.Namespace, client: VectorVeinClient) -> dict[str, Any]:
    info = client.get_user_info()
    return {
        "uid": str(info.get("uid", "")),
        "username": str(info.get("username", "")),
        "email": str(info.get("email", "")),
        "credits": int(info.get("credits", 0) or 0),
        "date_joined": str(info.get("date_joined", "")),
    }


def _cmd_user_info(args: argparse.Namespace, client: VectorVeinClient) -> dict[str, Any]:
    return client.get_user_info()


def _cmd_user_validate_api_key(args: argparse.Namespace, client: VectorVeinClient) -> dict[str, str]:
    identity = client.validate_api_key()
    return {"user_id": identity.user_id, "username": identity.username}


def _cmd_workflow_run(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    input_fields = _collect_workflow_input_fields(args)

    result = client.run_workflow(
        wid=args.wid,
        input_fields=input_fields,
        output_scope=args.output_scope,
        wait_for_completion=args.wait,
        api_key_type=args.api_key_type,
        timeout=args.timeout,
    )

    if isinstance(result, str):
        return {"rid": result, "status": "accepted", "wait_for_completion": False}
    return result


def _cmd_workflow_status(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.check_workflow_status(
        rid=args.rid,
        wid=args.wid,
        api_key_type=args.api_key_type,
    )


def _cmd_workflow_list(args: argparse.Namespace, client: VectorVeinClient) -> dict[str, Any]:
    return client.list_workflows(
        page=args.page,
        page_size=args.page_size,
        tags=args.tag or None,
        sort_field=args.sort_field,
        sort_order=args.sort_order,
        search_text=args.search_text,
    )


def _cmd_workflow_get(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_workflow(wid=args.wid)


def _cmd_task_agent_agent_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_agents(page=args.page, page_size=args.page_size, search=args.search)


def _cmd_task_agent_agent_get(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_agent(agent_id=args.agent_id)


def _cmd_task_agent_task_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    status_filter: str | list[str] | None = None
    if args.status:
        status_filter = args.status[0] if len(args.status) == 1 else args.status
    return client.list_agent_tasks(
        page=args.page,
        page_size=args.page_size,
        status=status_filter,
        agent_id=args.agent_id,
        search=args.search,
    )


def _cmd_task_agent_task_get(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_agent_task(task_id=args.task_id)


def _cmd_task_agent_task_create(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    if args.model_preference == "custom" and (not args.custom_backend_type or not args.custom_model_name):
        raise CLIUsageError("--model-preference custom requires both --custom-backend-type and --custom-model-name.")

    task_info = TaskInfo(
        text=args.text,
        attachments_detail=_collect_attachments(args),
        model_preference=args.model_preference,
        custom_backend_type=args.custom_backend_type,
        custom_model_name=args.custom_model_name,
    )

    return client.create_agent_task(
        task_info=task_info,
        agent_id_to_start=args.agent_id,
        agent_definition_to_start=_load_optional_agent_definition(args.agent_definition),
        agent_settings=_load_optional_agent_settings(args.agent_settings),
        max_cycles=args.max_cycles,
        title=args.title,
    )


def _cmd_task_agent_task_continue(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.continue_agent_task(
        task_id=args.task_id,
        message=args.message,
        attachments_detail=_collect_url_attachments(args),
    )


def _cmd_task_agent_task_pause(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.pause_agent_task(task_id=args.task_id)


def _cmd_task_agent_task_resume(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.resume_agent_task(
        task_id=args.task_id,
        message=args.message,
        attachments_detail=_collect_url_attachments(args),
    )


def _cmd_workspace_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_agent_workspaces(page=args.page, page_size=args.page_size)


def _cmd_workspace_get(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_agent_workspace(workspace_id=args.workspace_id)


def _cmd_workspace_files(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_workspace_files(
        workspace_id=args.workspace_id,
        prefix=args.prefix,
        tree_view=args.tree_view,
    )


def _cmd_workspace_read(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.read_workspace_file(
        workspace_id=args.workspace_id,
        file_path=args.file_path,
        start_line=args.start_line,
        end_line=args.end_line,
    )


def _cmd_workspace_write(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    use_inline = args.content is not None
    use_file = args.content_file is not None
    if use_inline == use_file:
        raise CLIUsageError("workspace write requires exactly one of --content or --content-file.")

    if use_file:
        path = Path(args.content_file)
        if not path.exists():
            raise CLIUsageError(f"--content-file does not exist: {path}")
        if not path.is_file():
            raise CLIUsageError(f"--content-file must be a file path: {path}")
        content = path.read_text(encoding="utf-8")
    else:
        content = str(args.content)

    return client.write_workspace_file(
        workspace_id=args.workspace_id,
        file_path=args.file_path,
        content=content,
    )


def _cmd_workspace_delete(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.delete_workspace_file(workspace_id=args.workspace_id, file_path=args.file_path)


def _cmd_workspace_download(args: argparse.Namespace, client: VectorVeinClient) -> dict[str, str]:
    file_url = client.download_workspace_file(workspace_id=args.workspace_id, file_path=args.file_path)
    return {"file_url": file_url}


def _cmd_workspace_zip(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.zip_workspace_files(workspace_id=args.workspace_id)


def _cmd_workspace_sync(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.sync_workspace_container_to_oss(workspace_id=args.workspace_id)


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


def _current_version() -> str:
    try:
        return package_version("vectorvein-sdk")
    except PackageNotFoundError:
        return "dev"


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


def build_parser() -> argparse.ArgumentParser:
    parser = CLIArgumentParser(
        prog="vectorvein",
        description=(
            "VectorVein command line interface.\n"
            "Default output is human-readable text.\n"
            "Use --format json for machine-readable responses.\n"
            "API key resolution order: --api-key > VECTORVEIN_API_KEY."
        ),
        epilog=(
            "Examples:\n"
            "  vectorvein auth whoami\n"
            "  vectorvein --format json auth whoami\n"
            '  vectorvein workflow run --wid wf_xxx --input-field \'{"node_id":"n1","field_name":"text","value":"Hello"}\'\n'
            "  vectorvein workflow status --rid rid_xxx\n"
            '  vectorvein task-agent task create --agent-id agent_xxx --text "Summarize this article"\n'
            "  vectorvein agent-workspace read --workspace-id ws_xxx --file-path notes.txt --start-line 1 --end-line 20\n"
            '  vectorvein api request --method POST --endpoint workflow/list --body \'{"page":1,"page_size":5}\'\n\n'
            "JSON inputs support @file syntax, for example --input-fields @payload.json.\n\n"
            "Exit codes:\n"
            "  0 success\n"
            "  1 unexpected error\n"
            "  2 invalid usage or arguments\n"
            "  3 authentication/API key error\n"
            "  4 API business error\n"
            "  5 network/request error"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--api-key", help=f"VectorVein API key. Overrides {ENV_API_KEY}.")
    parser.add_argument("--base-url", help=f"Open API base URL. Overrides {ENV_BASE_URL}.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format (default: text).")
    parser.add_argument("--compact", action="store_true", help="Output compact one-line JSON.")
    parser.add_argument("--debug", action="store_true", help="Include traceback details in error output.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {_current_version()}")

    top_level = parser.add_subparsers(dest="module")
    top_level.required = True

    auth_parser = top_level.add_parser("auth", help="Authentication related commands.")
    auth_sub = auth_parser.add_subparsers(dest="auth_command")
    auth_sub.required = True
    auth_whoami = auth_sub.add_parser(
        "whoami",
        help="Show current account profile summary.",
        description="Return account summary fields: uid, username, email, credits, date_joined.",
    )
    auth_whoami.set_defaults(handler=_cmd_auth_whoami, command="auth whoami")

    user_parser = top_level.add_parser("user", help="User profile commands.")
    user_sub = user_parser.add_subparsers(dest="user_command")
    user_sub.required = True
    user_info = user_sub.add_parser("info", help="Fetch current user profile (user-info/get).")
    user_info.set_defaults(handler=_cmd_user_info, command="user info")
    user_validate = user_sub.add_parser("validate-api-key", help="Validate API key (user/validate-api-key).")
    user_validate.set_defaults(handler=_cmd_user_validate_api_key, command="user validate-api-key")

    workflow_parser = top_level.add_parser("workflow", help="Workflow execution and query commands.")
    workflow_sub = workflow_parser.add_subparsers(dest="workflow_command")
    workflow_sub.required = True

    workflow_run = workflow_sub.add_parser(
        "run",
        help="Run a workflow and optionally wait for completion.",
        description=("Run a workflow.\nProvide input fields by repeating --input-field with JSON objects,\nor pass a JSON array using --input-fields."),
        epilog=(
            "Examples:\n"
            '  vectorvein workflow run --wid wf_x --input-field \'{"node_id":"n1","field_name":"text","value":"hello"}\'\n'
            "  vectorvein workflow run --wid wf_x --input-fields @inputs.json --wait --timeout 180\n"
            '  vectorvein workflow run --wid wf_x --input-fields \'[{"node_id":"n1","field_name":"text","value":"hello"}]\''
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    workflow_run.add_argument("--wid", required=True, help="Workflow ID.")
    workflow_run.add_argument(
        "--input-field",
        action="append",
        default=[],
        help="Single input field JSON object. Repeat this option for multiple fields.",
    )
    workflow_run.add_argument("--input-fields", help="JSON array or @file containing workflow input fields.")
    workflow_run.add_argument("--output-scope", choices=("all", "output_fields_only"), default="output_fields_only", help="Output detail scope.")
    workflow_run.add_argument("--wait", action="store_true", help="Wait until workflow finishes (polling).")
    workflow_run.add_argument("--timeout", type=int, default=300, help="Timeout in seconds when --wait is set.")
    workflow_run.add_argument("--api-key-type", choices=("WORKFLOW", "VAPP"), default="WORKFLOW", help="API key type header.")
    workflow_run.set_defaults(handler=_cmd_workflow_run, command="workflow run")

    workflow_status = workflow_sub.add_parser("status", help="Check workflow run status by rid.")
    workflow_status.add_argument("--rid", required=True, help="Workflow run record ID.")
    workflow_status.add_argument("--wid", help="Required only when --api-key-type is VAPP.")
    workflow_status.add_argument("--api-key-type", choices=("WORKFLOW", "VAPP"), default="WORKFLOW", help="API key type header.")
    workflow_status.set_defaults(handler=_cmd_workflow_status, command="workflow status")

    workflow_list = workflow_sub.add_parser("list", help="List workflows.")
    workflow_list.add_argument("--page", type=int, default=1, help="Page number.")
    workflow_list.add_argument("--page-size", type=int, default=10, help="Page size.")
    workflow_list.add_argument("--tag", action="append", default=[], help="Tag ID filter. Repeat for multiple tags.")
    workflow_list.add_argument("--search-text", help="Search text.")
    workflow_list.add_argument("--sort-field", default="update_time", help="Sort field.")
    workflow_list.add_argument("--sort-order", choices=("ascend", "descend"), default="descend", help="Sort order.")
    workflow_list.set_defaults(handler=_cmd_workflow_list, command="workflow list")

    workflow_get = workflow_sub.add_parser("get", help="Get workflow details.")
    workflow_get.add_argument("--wid", required=True, help="Workflow ID.")
    workflow_get.set_defaults(handler=_cmd_workflow_get, command="workflow get")

    task_agent_parser = top_level.add_parser("task-agent", help="Task-agent related commands.")
    task_agent_sub = task_agent_parser.add_subparsers(dest="task_agent_group")
    task_agent_sub.required = True

    task_agent_agent = task_agent_sub.add_parser("agent", help="Agent commands.")
    task_agent_agent_sub = task_agent_agent.add_subparsers(dest="task_agent_agent_command")
    task_agent_agent_sub.required = True

    task_agent_agent_list = task_agent_agent_sub.add_parser("list", help="List agents.")
    task_agent_agent_list.add_argument("--page", type=int, default=1, help="Page number.")
    task_agent_agent_list.add_argument("--page-size", type=int, default=10, help="Page size.")
    task_agent_agent_list.add_argument("--search", help="Search keyword.")
    task_agent_agent_list.set_defaults(handler=_cmd_task_agent_agent_list, command="task-agent agent list")

    task_agent_agent_get = task_agent_agent_sub.add_parser("get", help="Get one agent by ID.")
    task_agent_agent_get.add_argument("--agent-id", required=True, help="Agent ID.")
    task_agent_agent_get.set_defaults(handler=_cmd_task_agent_agent_get, command="task-agent agent get")

    task_agent_task = task_agent_sub.add_parser("task", help="Agent task commands.")
    task_agent_task_sub = task_agent_task.add_subparsers(dest="task_agent_task_command")
    task_agent_task_sub.required = True

    task_agent_task_list = task_agent_task_sub.add_parser("list", help="List agent tasks.")
    task_agent_task_list.add_argument("--page", type=int, default=1, help="Page number.")
    task_agent_task_list.add_argument("--page-size", type=int, default=10, help="Page size.")
    task_agent_task_list.add_argument("--status", action="append", help="Task status filter. Repeat to pass multiple status values.")
    task_agent_task_list.add_argument("--agent-id", help="Filter tasks by agent ID.")
    task_agent_task_list.add_argument("--search", help="Search keyword.")
    task_agent_task_list.set_defaults(handler=_cmd_task_agent_task_list, command="task-agent task list")

    task_agent_task_get = task_agent_task_sub.add_parser("get", help="Get one agent task by ID.")
    task_agent_task_get.add_argument("--task-id", required=True, help="Task ID.")
    task_agent_task_get.set_defaults(handler=_cmd_task_agent_task_get, command="task-agent task get")

    task_agent_task_create = task_agent_task_sub.add_parser(
        "create",
        help="Create an agent task.",
        description=(
            "Create an agent task.\n--attachment accepts JSON objects with exactly one of {url, oss_key}.\n--agent-definition and --agent-settings accept JSON objects or @file."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    task_agent_task_create.add_argument("--text", required=True, help="Task instruction text.")
    task_agent_task_create.add_argument("--agent-id", help="Agent ID to start.")
    task_agent_task_create.add_argument("--title", help="Optional task title.")
    task_agent_task_create.add_argument("--max-cycles", type=int, help="Override max cycles.")
    task_agent_task_create.add_argument(
        "--model-preference",
        choices=("default", "high_performance", "low_cost", "custom"),
        default="default",
        help="Task model preference.",
    )
    task_agent_task_create.add_argument("--custom-backend-type", help="Required when --model-preference is custom.")
    task_agent_task_create.add_argument("--custom-model-name", help="Required when --model-preference is custom.")
    task_agent_task_create.add_argument("--attachment", action="append", default=[], help="Single attachment JSON object. Repeat for multiple attachments.")
    task_agent_task_create.add_argument("--attachments", help="JSON array or @file for attachments.")
    task_agent_task_create.add_argument("--agent-definition", help="JSON object or @file for agent_definition_to_start.")
    task_agent_task_create.add_argument("--agent-settings", help="JSON object or @file for agent_settings.")
    task_agent_task_create.set_defaults(handler=_cmd_task_agent_task_create, command="task-agent task create")

    task_agent_task_continue = task_agent_task_sub.add_parser("continue", help="Continue an existing task with a new message.")
    task_agent_task_continue.add_argument("--task-id", required=True, help="Task ID.")
    task_agent_task_continue.add_argument("--message", required=True, help="New instruction or follow-up message.")
    task_agent_task_continue.add_argument("--attachment", action="append", default=[], help="Single attachment JSON object.")
    task_agent_task_continue.add_argument("--attachments", help="JSON array or @file for attachments.")
    task_agent_task_continue.set_defaults(handler=_cmd_task_agent_task_continue, command="task-agent task continue")

    task_agent_task_pause = task_agent_task_sub.add_parser("pause", help="Pause a running task.")
    task_agent_task_pause.add_argument("--task-id", required=True, help="Task ID.")
    task_agent_task_pause.set_defaults(handler=_cmd_task_agent_task_pause, command="task-agent task pause")

    task_agent_task_resume = task_agent_task_sub.add_parser("resume", help="Resume a paused task.")
    task_agent_task_resume.add_argument("--task-id", required=True, help="Task ID.")
    task_agent_task_resume.add_argument("--message", help="Optional message sent when resuming.")
    task_agent_task_resume.add_argument("--attachment", action="append", default=[], help="Single attachment JSON object.")
    task_agent_task_resume.add_argument("--attachments", help="JSON array or @file for attachments.")
    task_agent_task_resume.set_defaults(handler=_cmd_task_agent_task_resume, command="task-agent task resume")

    workspace_parser = top_level.add_parser("agent-workspace", help="Agent workspace commands.")
    workspace_sub = workspace_parser.add_subparsers(dest="workspace_command")
    workspace_sub.required = True

    workspace_list = workspace_sub.add_parser("list", help="List agent workspaces.")
    workspace_list.add_argument("--page", type=int, default=1, help="Page number.")
    workspace_list.add_argument("--page-size", type=int, default=10, help="Page size.")
    workspace_list.set_defaults(handler=_cmd_workspace_list, command="agent-workspace list")

    workspace_get = workspace_sub.add_parser("get", help="Get one workspace by ID.")
    workspace_get.add_argument("--workspace-id", required=True, help="Workspace ID.")
    workspace_get.set_defaults(handler=_cmd_workspace_get, command="agent-workspace get")

    workspace_files = workspace_sub.add_parser("files", help="List files in a workspace.")
    workspace_files.add_argument("--workspace-id", required=True, help="Workspace ID.")
    workspace_files.add_argument("--prefix", help="Path prefix filter.")
    workspace_files.add_argument("--tree-view", action="store_true", help="Return files in tree-view style.")
    workspace_files.set_defaults(handler=_cmd_workspace_files, command="agent-workspace files")

    workspace_read = workspace_sub.add_parser("read", help="Read a workspace file.")
    workspace_read.add_argument("--workspace-id", required=True, help="Workspace ID.")
    workspace_read.add_argument("--file-path", required=True, help="File path in workspace.")
    workspace_read.add_argument("--start-line", type=int, help="Start line (1-based).")
    workspace_read.add_argument("--end-line", type=int, help="End line (1-based, inclusive).")
    workspace_read.set_defaults(handler=_cmd_workspace_read, command="agent-workspace read")

    workspace_write = workspace_sub.add_parser("write", help="Write a workspace file.")
    workspace_write.add_argument("--workspace-id", required=True, help="Workspace ID.")
    workspace_write.add_argument("--file-path", required=True, help="File path in workspace.")
    workspace_write.add_argument("--content", help="Inline UTF-8 text content.")
    workspace_write.add_argument("--content-file", help="Read file content from local UTF-8 file.")
    workspace_write.set_defaults(handler=_cmd_workspace_write, command="agent-workspace write")

    workspace_delete = workspace_sub.add_parser("delete", help="Delete a workspace file.")
    workspace_delete.add_argument("--workspace-id", required=True, help="Workspace ID.")
    workspace_delete.add_argument("--file-path", required=True, help="File path in workspace.")
    workspace_delete.set_defaults(handler=_cmd_workspace_delete, command="agent-workspace delete")

    workspace_download = workspace_sub.add_parser("download", help="Get temporary download URL for a workspace file.")
    workspace_download.add_argument("--workspace-id", required=True, help="Workspace ID.")
    workspace_download.add_argument("--file-path", required=True, help="File path in workspace.")
    workspace_download.set_defaults(handler=_cmd_workspace_download, command="agent-workspace download")

    workspace_zip = workspace_sub.add_parser("zip", help="Zip entire workspace and return download metadata.")
    workspace_zip.add_argument("--workspace-id", required=True, help="Workspace ID.")
    workspace_zip.set_defaults(handler=_cmd_workspace_zip, command="agent-workspace zip")

    workspace_sync = workspace_sub.add_parser("sync", help="Trigger container-to-OSS sync for workspace.")
    workspace_sync.add_argument("--workspace-id", required=True, help="Workspace ID.")
    workspace_sync.set_defaults(handler=_cmd_workspace_sync, command="agent-workspace sync")

    api_parser = top_level.add_parser("api", help="Low-level API request command for unsupported operations.")
    api_sub = api_parser.add_subparsers(dest="api_command")
    api_sub.required = True
    api_request = api_sub.add_parser(
        "request",
        help="Send a raw request to Open API endpoint.",
        description=("Send a raw Open API request.\nUse this when a high-level CLI command is not available yet."),
        epilog=(
            "Examples:\n"
            '  vectorvein api request --method POST --endpoint workflow/list --body \'{"page":1,"page_size":10}\'\n'
            "  vectorvein api request --method GET --endpoint user-info/get\n"
            "  vectorvein api request --method POST --endpoint workflow/check-status --body @payload.json"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    api_request.add_argument("--method", choices=("GET", "POST", "PUT", "PATCH", "DELETE"), default="POST", help="HTTP method.")
    api_request.add_argument("--endpoint", required=True, help="Open API endpoint path, e.g. workflow/list.")
    api_request.add_argument("--params", help="JSON object or @file for query params.")
    api_request.add_argument("--body", help="JSON object or @file for request body.")
    api_request.add_argument("--api-key-type", choices=("WORKFLOW", "VAPP"), default="WORKFLOW", help="API key type header.")
    api_request.set_defaults(handler=_cmd_api_request, command="api request")

    return parser


def _run_with_client(args: argparse.Namespace) -> dict[str, Any]:
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
