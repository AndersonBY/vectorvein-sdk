"""Workflow parser builder."""

from __future__ import annotations

import argparse

from vectorvein.cli._builders.common import add_paging_arguments, add_search_argument, rich_parser_kwargs
from vectorvein.cli._commands.workflow import (
    _cmd_workflow_create,
    _cmd_workflow_delete,
    _cmd_workflow_describe,
    _cmd_workflow_get,
    _cmd_workflow_list,
    _cmd_workflow_run,
    _cmd_workflow_run_record_delete,
    _cmd_workflow_run_record_get,
    _cmd_workflow_run_record_list,
    _cmd_workflow_run_record_stop,
    _cmd_workflow_search,
    _cmd_workflow_status,
    _cmd_workflow_update,
)


def register_workflow_parser(top_level: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    workflow_parser = top_level.add_parser(
        "workflow",
        help="Workflow execution and query commands.",
        **rich_parser_kwargs(
            "Run, inspect, search, create, and update workflows from the command line.",
            examples=[
                "vectorvein workflow describe --wid wf_xxx",
                "vectorvein workflow run --wid wf_xxx --input-fields @inputs.json --wait",
                "vectorvein workflow search --query 'translation'",
            ],
        ),
    )
    workflow_sub = workflow_parser.add_subparsers(dest="workflow_command")
    workflow_sub.required = True

    workflow_run = workflow_sub.add_parser(
        "run",
        help="Run a workflow and optionally wait for completion.",
        **rich_parser_kwargs(
            """
            Run a workflow.
            Provide normal inputs via --input-field or --input-fields.
            For file fields, use --upload-to to upload local files and bind OSS paths into workflow input fields.
            """,
            examples=[
                'vectorvein workflow run --wid wf_x --input-field \'{"node_id":"n1","field_name":"text","value":"hello"}\'',
                "vectorvein workflow run --wid wf_x --input-fields @inputs.json --wait --timeout 180",
                "vectorvein workflow run --wid wf_x --upload-to n1:upload_files:./report.pdf",
            ],
            notes=[
                "--input-field accepts a single JSON object; repeat it for multiple fields.",
                "--input-fields accepts a JSON array or @file.",
                "--upload-to format: node_id:field_name:local_file_path",
            ],
        ),
    )
    workflow_run.add_argument("--wid", required=True, help="Workflow ID.")
    workflow_run.add_argument("--input-field", action="append", default=[], help="Single input field JSON object. Repeat this option for multiple fields.")
    workflow_run.add_argument("--input-fields", help="JSON array or @file containing workflow input fields.")
    workflow_run.add_argument("--output-scope", choices=("all", "output_fields_only"), default="output_fields_only", help="Output detail scope (default: output_fields_only).")
    workflow_run.add_argument("--wait", action="store_true", help="Wait until the workflow finishes (polling).")
    workflow_run.add_argument("--timeout", type=int, default=300, help="Timeout in seconds when --wait is set (default: 300).")
    workflow_run.add_argument("--api-key-type", choices=("WORKFLOW", "VAPP"), default="WORKFLOW", help="API key type header (default: WORKFLOW).")
    workflow_run.add_argument("--upload-to", action="append", default=[], help="Upload file and bind to field. Format: node_id:field_name:local_file_path.")
    workflow_run.add_argument("--upload-as", choices=("auto", "single", "list"), default="auto", help="How uploaded paths map to the workflow field value.")
    workflow_run.set_defaults(handler=_cmd_workflow_run, command="workflow run")

    workflow_status = workflow_sub.add_parser(
        "status",
        help="Check workflow run status by rid.",
        **rich_parser_kwargs("Check workflow execution status by run record ID.", examples=["vectorvein workflow status --rid rid_xxx"]),
    )
    workflow_status.add_argument("--rid", required=True, help="Workflow run record ID.")
    workflow_status.add_argument("--wid", help="Required only when --api-key-type is VAPP.")
    workflow_status.add_argument("--api-key-type", choices=("WORKFLOW", "VAPP"), default="WORKFLOW", help="API key type header (default: WORKFLOW).")
    workflow_status.set_defaults(handler=_cmd_workflow_status, command="workflow status")

    workflow_list = workflow_sub.add_parser(
        "list",
        help="List workflows.",
        **rich_parser_kwargs("List workflows owned by or visible to the current account.", examples=["vectorvein workflow list --page 1 --page-size 20"]),
    )
    add_paging_arguments(workflow_list)
    workflow_list.add_argument("--tag", action="append", default=[], help="Tag ID filter. Repeat for multiple tags.")
    add_search_argument(workflow_list, option="--search-text", help_text="Search text.")
    workflow_list.add_argument("--sort-field", default="update_time", help="Sort field (default: update_time).")
    workflow_list.add_argument("--sort-order", choices=("ascend", "descend"), default="descend", help="Sort order (default: descend).")
    workflow_list.set_defaults(handler=_cmd_workflow_list, command="workflow list")

    workflow_get = workflow_sub.add_parser(
        "get",
        help="Get workflow details (full data).",
        **rich_parser_kwargs("Fetch the full workflow definition, including nodes and edges.", examples=["vectorvein workflow get --wid wf_xxx"]),
    )
    workflow_get.add_argument("--wid", required=True, help="Workflow ID.")
    workflow_get.set_defaults(handler=_cmd_workflow_get, command="workflow get")

    workflow_describe = workflow_sub.add_parser(
        "describe",
        help="Describe a workflow's input fields (agent-friendly).",
        **rich_parser_kwargs(
            """
            Show a workflow's title, brief, and all user-facing input fields.
            Use this before `workflow run` to discover what inputs are required.
            """,
            examples=["vectorvein workflow describe --wid wf_xxx"],
        ),
    )
    workflow_describe.add_argument("--wid", required=True, help="Workflow ID.")
    workflow_describe.set_defaults(handler=_cmd_workflow_describe, command="workflow describe")

    workflow_create = workflow_sub.add_parser(
        "create",
        help="Create a new workflow.",
        **rich_parser_kwargs(
            "Create a new workflow. Use --source-wid to clone an existing workflow and --data to provide the initial graph.",
            examples=[
                "vectorvein workflow create --title 'My Workflow'",
                "vectorvein workflow create --title 'My Workflow' --source-wid wf_xxx",
            ],
            notes=["--data accepts a workflow JSON object or @file."],
        ),
    )
    workflow_create.add_argument("--title", help="Workflow title (default: New workflow).")
    workflow_create.add_argument("--brief", help="Workflow brief description or @file.")
    workflow_create.add_argument("--language", help="Workflow language (default: zh-CN).")
    workflow_create.add_argument("--data", help="JSON object or @file for workflow graph data.")
    workflow_create.add_argument("--source-wid", help="Source workflow ID to copy from.")
    workflow_create.set_defaults(handler=_cmd_workflow_create, command="workflow create")

    workflow_update = workflow_sub.add_parser(
        "update",
        help="Update an existing workflow.",
        **rich_parser_kwargs(
            "Update a workflow. Provide the full workflow graph via --data when editing nodes or edges.",
            examples=["vectorvein workflow update --wid wf_xxx --data @workflow.json --title 'Renamed Workflow'"],
            notes=["--data accepts a workflow JSON object or @file."],
        ),
    )
    workflow_update.add_argument("--wid", required=True, help="Workflow ID.")
    workflow_update.add_argument("--data", required=True, help="JSON object or @file for workflow graph data.")
    workflow_update.add_argument("--title", help="New workflow title.")
    workflow_update.add_argument("--brief", help="New workflow brief description or @file.")
    workflow_update.add_argument("--language", help="New workflow language.")
    workflow_update.set_defaults(handler=_cmd_workflow_update, command="workflow update")

    workflow_delete = workflow_sub.add_parser(
        "delete",
        help="Delete a workflow.",
        **rich_parser_kwargs("Delete a workflow by ID.", examples=["vectorvein workflow delete --wid wf_xxx"]),
    )
    workflow_delete.add_argument("--wid", required=True, help="Workflow ID.")
    workflow_delete.set_defaults(handler=_cmd_workflow_delete, command="workflow delete")

    workflow_search = workflow_sub.add_parser(
        "search",
        help="Search workflows by keyword.",
        **rich_parser_kwargs("Search workflows by keyword.", examples=["vectorvein workflow search --query translation"]),
    )
    workflow_search.add_argument("--query", required=True, help="Search keyword.")
    add_paging_arguments(workflow_search)
    workflow_search.add_argument("--tag", action="append", default=[], help="Tag ID filter. Repeat for multiple tags.")
    workflow_search.add_argument("--sort-field", default="update_time", help="Sort field (default: update_time).")
    workflow_search.add_argument("--sort-order", choices=("ascend", "descend"), default="descend", help="Sort order (default: descend).")
    workflow_search.set_defaults(handler=_cmd_workflow_search, command="workflow search")

    workflow_run_record = workflow_sub.add_parser(
        "run-record",
        help="Workflow run record commands.",
        **rich_parser_kwargs(
            "Inspect, fetch, stop, and delete workflow run records.",
            examples=[
                "vectorvein workflow run-record list --wid wf_xxx",
                "vectorvein workflow run-record get --rid rid_xxx",
            ],
        ),
    )
    workflow_run_record_sub = workflow_run_record.add_subparsers(dest="workflow_run_record_command")
    workflow_run_record_sub.required = True

    workflow_rr_list = workflow_run_record_sub.add_parser(
        "list",
        help="List workflow run records.",
        **rich_parser_kwargs(
            "List workflow run records, optionally filtered by workflow ID or status.", examples=["vectorvein workflow run-record list --wid wf_xxx --status FINISHED"]
        ),
    )
    workflow_rr_list.add_argument("--wid", help="Filter by workflow ID.")
    workflow_rr_list.add_argument("--status", action="append", help="Status filter such as FINISHED, FAILED, or RUNNING. Repeat for multiple.")
    add_paging_arguments(workflow_rr_list)
    workflow_rr_list.add_argument("--sort-field", default="start_time", help="Sort field (default: start_time).")
    workflow_rr_list.add_argument("--sort-order", choices=("ascend", "descend"), default="descend", help="Sort order (default: descend).")
    workflow_rr_list.set_defaults(handler=_cmd_workflow_run_record_list, command="workflow run-record list")

    workflow_rr_get = workflow_run_record_sub.add_parser(
        "get",
        help="Get a workflow run record by rid.",
        **rich_parser_kwargs("Fetch a workflow run record by run record ID.", examples=["vectorvein workflow run-record get --rid rid_xxx"]),
    )
    workflow_rr_get.add_argument("--rid", required=True, help="Workflow run record ID.")
    workflow_rr_get.set_defaults(handler=_cmd_workflow_run_record_get, command="workflow run-record get")

    workflow_rr_delete = workflow_run_record_sub.add_parser(
        "delete",
        help="Delete a workflow run record.",
        **rich_parser_kwargs("Delete a workflow run record by run record ID.", examples=["vectorvein workflow run-record delete --rid rid_xxx"]),
    )
    workflow_rr_delete.add_argument("--rid", required=True, help="Workflow run record ID.")
    workflow_rr_delete.set_defaults(handler=_cmd_workflow_run_record_delete, command="workflow run-record delete")

    workflow_rr_stop = workflow_run_record_sub.add_parser(
        "stop",
        help="Stop a running workflow execution.",
        **rich_parser_kwargs("Stop a running workflow execution by run record ID.", examples=["vectorvein workflow run-record stop --rid rid_xxx"]),
    )
    workflow_rr_stop.add_argument("--rid", required=True, help="Workflow run record ID.")
    workflow_rr_stop.set_defaults(handler=_cmd_workflow_run_record_stop, command="workflow run-record stop")
