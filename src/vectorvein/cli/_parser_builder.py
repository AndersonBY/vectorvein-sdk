"""Build the CLI argument parser and register all sub-commands."""

from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, version as package_version

from vectorvein.cli._output import CLIArgumentParser
from vectorvein.cli._parsers import ENV_API_KEY, ENV_BASE_URL

from vectorvein.cli._commands.auth import (
    _cmd_auth_whoami,
    _cmd_user_info,
    _cmd_user_validate_api_key,
)
from vectorvein.cli._commands.workflow import (
    _cmd_workflow_run,
    _cmd_workflow_status,
    _cmd_workflow_list,
    _cmd_workflow_get,
    _cmd_workflow_describe,
    _cmd_workflow_create,
    _cmd_workflow_update,
    _cmd_workflow_delete,
    _cmd_workflow_search,
    _cmd_workflow_run_record_list,
    _cmd_workflow_run_record_get,
    _cmd_workflow_run_record_delete,
    _cmd_workflow_run_record_stop,
)
from vectorvein.cli._commands.task_agent import (
    _cmd_task_agent_agent_list,
    _cmd_task_agent_agent_get,
    _cmd_task_agent_agent_create,
    _cmd_task_agent_agent_update,
    _cmd_task_agent_agent_delete,
    _cmd_task_agent_agent_search,
    _cmd_task_agent_task_list,
    _cmd_task_agent_task_get,
    _cmd_task_agent_task_create,
    _cmd_task_agent_task_continue,
    _cmd_task_agent_task_pause,
    _cmd_task_agent_task_resume,
    _cmd_task_agent_task_respond,
    _cmd_task_agent_task_delete,
    _cmd_task_agent_task_search,
    _cmd_task_agent_cycle_list,
    _cmd_task_agent_cycle_get,
)
from vectorvein.cli._commands.workspace import (
    _cmd_workspace_list,
    _cmd_workspace_get,
    _cmd_workspace_files,
    _cmd_workspace_read,
    _cmd_workspace_write,
    _cmd_workspace_delete,
    _cmd_workspace_download,
    _cmd_workspace_zip,
    _cmd_workspace_sync,
)
from vectorvein.cli._commands.file import _cmd_file_upload
from vectorvein.cli._commands.api import _cmd_api_request


def _current_version() -> str:
    try:
        return package_version("vectorvein-sdk")
    except PackageNotFoundError:
        return "dev"


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
            "  vectorvein workflow run --wid wf_xxx --upload-to n1:upload_files:./report.pdf\n"
            "  vectorvein workflow search --query 'translation'\n"
            "  vectorvein workflow create --title 'My Workflow' --source-wid wf_xxx\n"
            "  vectorvein file upload --path ./report.pdf --path ./appendix.pdf\n"
            "  vectorvein workflow status --rid rid_xxx\n"
            '  vectorvein task-agent task create --agent-id agent_xxx --text "Summarize this article" --wait\n'
            '  vectorvein task-agent task respond --task-id t_xxx --tool-call-id tc_xxx --response "Yes, proceed"\n'
            "  vectorvein task-agent agent search --query 'translator'\n"
            "  vectorvein task-agent cycle list --task-id t_xxx\n"
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
        description=(
            "Run a workflow.\n"
            "Provide normal inputs via --input-field/--input-fields.\n"
            "For file fields, use --upload-to to upload local files and bind OSS paths into workflow input fields."
        ),
        epilog=(
            "Examples:\n"
            '  vectorvein workflow run --wid wf_x --input-field \'{"node_id":"n1","field_name":"text","value":"hello"}\'\n'
            "  vectorvein workflow run --wid wf_x --input-fields @inputs.json --wait --timeout 180\n"
            '  vectorvein workflow run --wid wf_x --input-fields \'[{"node_id":"n1","field_name":"text","value":"hello"}]\'\n'
            "  vectorvein workflow run --wid wf_x --upload-to n1:upload_files:./report.pdf\n"
            "  vectorvein workflow run --wid wf_x --upload-to n1:upload_files:./a.pdf --upload-to n1:upload_files:./b.pdf --upload-as list"
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
    workflow_run.add_argument(
        "--upload-to",
        action="append",
        default=[],
        help="Upload file and bind to field. Format: node_id:field_name:local_file_path. Repeat for multiple files.",
    )
    workflow_run.add_argument(
        "--upload-as",
        choices=("auto", "single", "list"),
        default="auto",
        help="How uploaded paths map to field value (default: auto).",
    )
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

    workflow_get = workflow_sub.add_parser("get", help="Get workflow details (full data).")
    workflow_get.add_argument("--wid", required=True, help="Workflow ID.")
    workflow_get.set_defaults(handler=_cmd_workflow_get, command="workflow get")

    workflow_describe = workflow_sub.add_parser(
        "describe",
        help="Describe a workflow's input fields (agent-friendly).",
        description=(
            "Show a workflow's title, brief, and all user-facing input fields.\n"
            "Each input field includes node_id, field_name, field_type, required, and default value.\n"
            "Use this before 'workflow run' to discover what inputs are needed."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    workflow_describe.add_argument("--wid", required=True, help="Workflow ID.")
    workflow_describe.set_defaults(handler=_cmd_workflow_describe, command="workflow describe")

    workflow_create = workflow_sub.add_parser(
        "create",
        help="Create a new workflow.",
        description="Create a new workflow. Use --source-wid to copy from an existing workflow.",
    )
    workflow_create.add_argument("--title", help="Workflow title (default: 'New workflow').")
    workflow_create.add_argument("--brief", help="Workflow brief description.")
    workflow_create.add_argument("--language", help="Workflow language (default: zh-CN).")
    workflow_create.add_argument("--data", help="JSON object or @file for workflow data (nodes/edges).")
    workflow_create.add_argument("--source-wid", help="Source workflow ID to copy from.")
    workflow_create.set_defaults(handler=_cmd_workflow_create, command="workflow create")

    workflow_update = workflow_sub.add_parser(
        "update",
        help="Update an existing workflow.",
        description="Update a workflow. --data is required and contains the full workflow data.",
    )
    workflow_update.add_argument("--wid", required=True, help="Workflow ID.")
    workflow_update.add_argument("--data", required=True, help="JSON object or @file for workflow data (nodes/edges).")
    workflow_update.add_argument("--title", help="New workflow title.")
    workflow_update.add_argument("--brief", help="New brief description.")
    workflow_update.add_argument("--language", help="New language.")
    workflow_update.set_defaults(handler=_cmd_workflow_update, command="workflow update")

    workflow_delete = workflow_sub.add_parser("delete", help="Delete a workflow.")
    workflow_delete.add_argument("--wid", required=True, help="Workflow ID.")
    workflow_delete.set_defaults(handler=_cmd_workflow_delete, command="workflow delete")

    workflow_search = workflow_sub.add_parser("search", help="Search workflows by keyword.")
    workflow_search.add_argument("--query", required=True, help="Search keyword.")
    workflow_search.add_argument("--page", type=int, default=1, help="Page number.")
    workflow_search.add_argument("--page-size", type=int, default=10, help="Page size.")
    workflow_search.add_argument("--tag", action="append", default=[], help="Tag ID filter. Repeat for multiple tags.")
    workflow_search.add_argument("--sort-field", default="update_time", help="Sort field.")
    workflow_search.add_argument("--sort-order", choices=("ascend", "descend"), default="descend", help="Sort order.")
    workflow_search.set_defaults(handler=_cmd_workflow_search, command="workflow search")

    workflow_run_record = workflow_sub.add_parser("run-record", help="Workflow run record commands.")
    workflow_run_record_sub = workflow_run_record.add_subparsers(dest="workflow_run_record_command")
    workflow_run_record_sub.required = True

    workflow_rr_list = workflow_run_record_sub.add_parser("list", help="List workflow run records.")
    workflow_rr_list.add_argument("--wid", help="Filter by workflow ID.")
    workflow_rr_list.add_argument("--status", action="append", help="Status filter (e.g. FINISHED, FAILED, RUNNING). Repeat for multiple.")
    workflow_rr_list.add_argument("--page", type=int, default=1, help="Page number.")
    workflow_rr_list.add_argument("--page-size", type=int, default=10, help="Page size.")
    workflow_rr_list.add_argument("--sort-field", default="start_time", help="Sort field (default: start_time).")
    workflow_rr_list.add_argument("--sort-order", choices=("ascend", "descend"), default="descend", help="Sort order.")
    workflow_rr_list.set_defaults(handler=_cmd_workflow_run_record_list, command="workflow run-record list")

    workflow_rr_get = workflow_run_record_sub.add_parser("get", help="Get a workflow run record by rid.")
    workflow_rr_get.add_argument("--rid", required=True, help="Workflow run record ID.")
    workflow_rr_get.set_defaults(handler=_cmd_workflow_run_record_get, command="workflow run-record get")

    workflow_rr_delete = workflow_run_record_sub.add_parser("delete", help="Delete a workflow run record.")
    workflow_rr_delete.add_argument("--rid", required=True, help="Workflow run record ID.")
    workflow_rr_delete.set_defaults(handler=_cmd_workflow_run_record_delete, command="workflow run-record delete")

    workflow_rr_stop = workflow_run_record_sub.add_parser("stop", help="Stop a running workflow execution.")
    workflow_rr_stop.add_argument("--rid", required=True, help="Workflow run record ID.")
    workflow_rr_stop.set_defaults(handler=_cmd_workflow_run_record_stop, command="workflow run-record stop")

    file_parser = top_level.add_parser("file", help="File upload commands.")
    file_sub = file_parser.add_subparsers(dest="file_command")
    file_sub.required = True

    file_upload = file_sub.add_parser("upload", help="Upload local file(s) and return OSS path(s).")
    file_upload.add_argument("--path", action="append", required=True, help="Local file path to upload. Repeat for multiple files.")
    file_upload.set_defaults(handler=_cmd_file_upload, command="file upload")

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

    task_agent_agent_create = task_agent_agent_sub.add_parser(
        "create",
        help="Create a new agent.",
        description="Create a new agent with a name and optional configuration.",
    )
    task_agent_agent_create.add_argument("--name", required=True, help="Agent name.")
    task_agent_agent_create.add_argument("--description", help="Agent description.")
    task_agent_agent_create.add_argument("--system-prompt", help="System prompt (default: 'You are a helpful assistant.').")
    task_agent_agent_create.add_argument("--model-name", help="Default model name.")
    task_agent_agent_create.add_argument("--backend-type", help="Default backend type.")
    task_agent_agent_create.add_argument("--max-cycles", type=int, help="Default max cycles (default: 20).")
    task_agent_agent_create.set_defaults(handler=_cmd_task_agent_agent_create, command="task-agent agent create")

    task_agent_agent_update = task_agent_agent_sub.add_parser(
        "update",
        help="Update an existing agent.",
        description="Update agent fields. Only provided fields are changed.",
    )
    task_agent_agent_update.add_argument("--agent-id", required=True, help="Agent ID.")
    task_agent_agent_update.add_argument("--name", help="New agent name.")
    task_agent_agent_update.add_argument("--description", help="New description.")
    task_agent_agent_update.add_argument("--system-prompt", help="New system prompt.")
    task_agent_agent_update.add_argument("--model-name", help="New default model name.")
    task_agent_agent_update.add_argument("--backend-type", help="New default backend type.")
    task_agent_agent_update.add_argument("--max-cycles", type=int, help="New default max cycles.")
    task_agent_agent_update.set_defaults(handler=_cmd_task_agent_agent_update, command="task-agent agent update")

    task_agent_agent_delete = task_agent_agent_sub.add_parser("delete", help="Delete an agent.")
    task_agent_agent_delete.add_argument("--agent-id", required=True, help="Agent ID.")
    task_agent_agent_delete.set_defaults(handler=_cmd_task_agent_agent_delete, command="task-agent agent delete")

    task_agent_agent_search = task_agent_agent_sub.add_parser("search", help="Search agents by keyword.")
    task_agent_agent_search.add_argument("--query", required=True, help="Search keyword.")
    task_agent_agent_search.add_argument("--page", type=int, default=1, help="Page number.")
    task_agent_agent_search.add_argument("--page-size", type=int, default=10, help="Page size.")
    task_agent_agent_search.set_defaults(handler=_cmd_task_agent_agent_search, command="task-agent agent search")

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
    task_agent_task_create.add_argument("--wait", action="store_true", help="Wait until task finishes, fails, or needs human response (polling).")
    task_agent_task_create.add_argument("--timeout", type=int, default=600, help="Timeout in seconds when --wait is set (default: 600).")
    task_agent_task_create.set_defaults(handler=_cmd_task_agent_task_create, command="task-agent task create")

    task_agent_task_continue = task_agent_task_sub.add_parser("continue", help="Continue an existing task with a new message.")
    task_agent_task_continue.add_argument("--task-id", required=True, help="Task ID.")
    task_agent_task_continue.add_argument("--message", required=True, help="New instruction or follow-up message.")
    task_agent_task_continue.add_argument("--attachment", action="append", default=[], help="Single attachment JSON object.")
    task_agent_task_continue.add_argument("--attachments", help="JSON array or @file for attachments.")
    task_agent_task_continue.add_argument("--wait", action="store_true", help="Wait until task finishes, fails, or needs human response.")
    task_agent_task_continue.add_argument("--timeout", type=int, default=600, help="Timeout in seconds when --wait is set (default: 600).")
    task_agent_task_continue.set_defaults(handler=_cmd_task_agent_task_continue, command="task-agent task continue")

    task_agent_task_pause = task_agent_task_sub.add_parser("pause", help="Pause a running task.")
    task_agent_task_pause.add_argument("--task-id", required=True, help="Task ID.")
    task_agent_task_pause.set_defaults(handler=_cmd_task_agent_task_pause, command="task-agent task pause")

    task_agent_task_resume = task_agent_task_sub.add_parser("resume", help="Resume a paused task.")
    task_agent_task_resume.add_argument("--task-id", required=True, help="Task ID.")
    task_agent_task_resume.add_argument("--message", help="Optional message sent when resuming.")
    task_agent_task_resume.add_argument("--attachment", action="append", default=[], help="Single attachment JSON object.")
    task_agent_task_resume.add_argument("--attachments", help="JSON array or @file for attachments.")
    task_agent_task_resume.add_argument("--wait", action="store_true", help="Wait until task finishes, fails, or needs human response.")
    task_agent_task_resume.add_argument("--timeout", type=int, default=600, help="Timeout in seconds when --wait is set (default: 600).")
    task_agent_task_resume.set_defaults(handler=_cmd_task_agent_task_resume, command="task-agent task resume")

    task_agent_task_respond = task_agent_task_sub.add_parser(
        "respond",
        help="Respond to a waiting task's question (human-in-the-loop).",
        description="When a task status is 'waiting', use this command to answer the agent's question.",
    )
    task_agent_task_respond.add_argument("--task-id", required=True, help="Task ID.")
    task_agent_task_respond.add_argument("--tool-call-id", required=True, help="Tool call ID from the waiting_question.")
    task_agent_task_respond.add_argument("--response", required=True, help="Response content to the agent's question.")
    task_agent_task_respond.add_argument("--wait", action="store_true", help="Wait until task finishes, fails, or needs another question.")
    task_agent_task_respond.add_argument("--timeout", type=int, default=600, help="Timeout in seconds when --wait is set (default: 600).")
    task_agent_task_respond.set_defaults(handler=_cmd_task_agent_task_respond, command="task-agent task respond")

    task_agent_task_delete = task_agent_task_sub.add_parser("delete", help="Delete an agent task.")
    task_agent_task_delete.add_argument("--task-id", required=True, help="Task ID.")
    task_agent_task_delete.set_defaults(handler=_cmd_task_agent_task_delete, command="task-agent task delete")

    task_agent_task_search = task_agent_task_sub.add_parser("search", help="Search agent tasks by keyword.")
    task_agent_task_search.add_argument("--query", required=True, help="Search keyword.")
    task_agent_task_search.add_argument("--page", type=int, default=1, help="Page number.")
    task_agent_task_search.add_argument("--page-size", type=int, default=10, help="Page size.")
    task_agent_task_search.add_argument("--status", action="append", help="Task status filter. Repeat for multiple.")
    task_agent_task_search.add_argument("--agent-id", help="Filter tasks by agent ID.")
    task_agent_task_search.set_defaults(handler=_cmd_task_agent_task_search, command="task-agent task search")

    task_agent_cycle = task_agent_sub.add_parser("cycle", help="Agent cycle (reasoning step) commands.")
    task_agent_cycle_sub = task_agent_cycle.add_subparsers(dest="task_agent_cycle_command")
    task_agent_cycle_sub.required = True

    task_agent_cycle_list = task_agent_cycle_sub.add_parser("list", help="List cycles for an agent task.")
    task_agent_cycle_list.add_argument("--task-id", required=True, help="Task ID.")
    task_agent_cycle_list.add_argument("--offset", type=int, default=0, help="Cycle index offset.")
    task_agent_cycle_list.set_defaults(handler=_cmd_task_agent_cycle_list, command="task-agent cycle list")

    task_agent_cycle_get = task_agent_cycle_sub.add_parser("get", help="Get one cycle by ID.")
    task_agent_cycle_get.add_argument("--cycle-id", required=True, help="Cycle ID.")
    task_agent_cycle_get.set_defaults(handler=_cmd_task_agent_cycle_get, command="task-agent cycle get")

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
