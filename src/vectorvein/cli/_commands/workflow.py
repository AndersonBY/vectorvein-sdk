"""Workflow command handlers."""

from __future__ import annotations

import argparse
from typing import Any

from vectorvein.api import VectorVeinClient

from vectorvein.cli._output import CLIUsageError
from vectorvein.cli._parsers import (
    _collect_optional_workflow_input_fields,
    _collect_uploaded_workflow_input_fields,
    _load_json_object,
    _load_optional_text_value,
)

WORKFLOW_LIST_HIDDEN_FIELDS = {
    "language",
    "images",
    "is_fast_access",
    "browser_settings",
    "chrome_settings",
    "use_in_wechat",
}


def _trim_workflow_list_fields(data: dict[str, Any]) -> dict[str, Any]:
    workflows = data.get("workflows")
    if not isinstance(workflows, list):
        return data

    trimmed_workflows: list[Any] = []
    for workflow in workflows:
        if isinstance(workflow, dict):
            trimmed_workflows.append({key: value for key, value in workflow.items() if key not in WORKFLOW_LIST_HIDDEN_FIELDS})
        else:
            trimmed_workflows.append(workflow)

    result = dict(data)
    result["workflows"] = trimmed_workflows
    return result


def _cmd_workflow_run(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    explicit_input_fields = _collect_optional_workflow_input_fields(args)
    uploaded_input_fields = _collect_uploaded_workflow_input_fields(args, client)
    input_fields = explicit_input_fields + uploaded_input_fields
    if not input_fields:
        raise CLIUsageError("No workflow input fields provided. Use --input-field/--input-fields, or --upload-to for file-based inputs.")

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
    response = client.list_workflows(
        page=args.page,
        page_size=args.page_size,
        tags=args.tag or None,
        sort_field=args.sort_field,
        sort_order=args.sort_order,
        search_text=args.search_text,
    )
    return _trim_workflow_list_fields(response)


def _cmd_workflow_get(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_workflow(wid=args.wid)


def _extract_workflow_input_fields(workflow_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract user-facing input fields from workflow graph data."""
    input_fields: list[dict[str, Any]] = []
    nodes = workflow_data.get("nodes", [])
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id = node.get("id", "")
        node_data = node.get("data", {})
        template = node_data.get("template", {})
        if not isinstance(template, dict):
            continue
        for field_name, field_def in template.items():
            if not isinstance(field_def, dict):
                continue
            if field_def.get("is_output", False):
                continue
            if not field_def.get("show", True):
                continue
            field_info: dict[str, Any] = {
                "node_id": node_id,
                "field_name": field_name,
                "display_name": field_def.get("display_name", field_name),
                "field_type": field_def.get("field_type", ""),
                "required": field_def.get("required", False),
            }
            if "value" in field_def and field_def["value"] not in (None, "", []):
                field_info["default"] = field_def["value"]
            if "options" in field_def:
                field_info["options"] = field_def["options"]
            input_fields.append(field_info)
    return input_fields


def _cmd_workflow_describe(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    workflow = client.get_workflow(wid=args.wid)
    data = workflow.data if hasattr(workflow, "data") else {}
    input_fields = _extract_workflow_input_fields(data) if isinstance(data, dict) else []
    result: dict[str, Any] = {
        "wid": workflow.wid if hasattr(workflow, "wid") else args.wid,
        "title": workflow.title if hasattr(workflow, "title") else "",
        "brief": workflow.brief if hasattr(workflow, "brief") else "",
        "input_fields": input_fields,
    }
    return result


def _cmd_workflow_create(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    kwargs: dict[str, Any] = {}
    if args.title is not None:
        kwargs["title"] = args.title
    if args.brief is not None:
        kwargs["brief"] = _load_optional_text_value(args.brief, "--brief")
    if args.language is not None:
        kwargs["language"] = args.language
    if args.data is not None:
        kwargs["data"] = _load_json_object(args.data, "--data")
    if args.source_wid is not None:
        kwargs["source_workflow_wid"] = args.source_wid
    return client.create_workflow(**kwargs)


def _cmd_workflow_update(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    data = _load_json_object(args.data, "--data")
    kwargs: dict[str, Any] = {"wid": args.wid, "data": data}
    if args.title is not None:
        kwargs["title"] = args.title
    if args.brief is not None:
        kwargs["brief"] = _load_optional_text_value(args.brief, "--brief")
    if args.language is not None:
        kwargs["language"] = args.language
    return client.update_workflow(**kwargs)


def _cmd_workflow_delete(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    result = client.delete_workflow(wid=args.wid)
    return result if result else {"deleted": True, "wid": args.wid}


def _cmd_workflow_search(args: argparse.Namespace, client: VectorVeinClient) -> dict[str, Any]:
    response = client.list_workflows(
        page=args.page,
        page_size=args.page_size,
        tags=args.tag or None,
        sort_field=args.sort_field,
        sort_order=args.sort_order,
        search_text=args.query,
    )
    return _trim_workflow_list_fields(response)


def _cmd_workflow_run_record_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    status_filter: list[str] | None = args.status or None
    return client.list_workflow_run_records(
        page=args.page,
        page_size=args.page_size,
        wid=args.wid,
        status=status_filter,
        sort_field=args.sort_field,
        sort_order=args.sort_order,
    )


def _cmd_workflow_run_record_get(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_workflow_run_record(rid=args.rid)


def _cmd_workflow_run_record_delete(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    result = client.delete_workflow_run_record(rid=args.rid)
    return result if result else {"deleted": True, "rid": args.rid}


def _cmd_workflow_run_record_stop(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.stop_workflow_run_record(rid=args.rid)
