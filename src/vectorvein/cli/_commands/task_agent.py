"""Task-agent command handlers (agent, task, cycle CRUD + search + poll)."""

from __future__ import annotations

import argparse
from typing import Any

from vectorvein.api import TaskInfo, VectorVeinClient

from vectorvein.cli._output import CLIUsageError
from vectorvein.cli._parsers import (
    _collect_attachments,
    _collect_url_attachments,
    _load_optional_agent_definition,
    _load_optional_agent_settings,
    _poll_task_until_done,
)


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

    result = client.create_agent_task(
        task_info=task_info,
        agent_id_to_start=args.agent_id,
        agent_definition_to_start=_load_optional_agent_definition(args.agent_definition),
        agent_settings=_load_optional_agent_settings(args.agent_settings),
        max_cycles=args.max_cycles,
        title=args.title,
    )

    if not args.wait:
        return result

    return _poll_task_until_done(client, result.task_id, args.timeout)


def _cmd_task_agent_task_continue(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    result = client.continue_agent_task(
        task_id=args.task_id,
        message=args.message,
        attachments_detail=_collect_url_attachments(args),
    )
    if not args.wait:
        return result
    return _poll_task_until_done(client, args.task_id, args.timeout)


def _cmd_task_agent_task_pause(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.pause_agent_task(task_id=args.task_id)


def _cmd_task_agent_task_resume(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    result = client.resume_agent_task(
        task_id=args.task_id,
        message=args.message,
        attachments_detail=_collect_url_attachments(args),
    )
    if not args.wait:
        return result
    return _poll_task_until_done(client, args.task_id, args.timeout)


def _cmd_task_agent_task_respond(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    result = client.respond_to_agent_task(
        task_id=args.task_id,
        tool_call_id=args.tool_call_id,
        response_content=args.response,
    )
    if not args.wait:
        return result
    return _poll_task_until_done(client, args.task_id, args.timeout)


def _cmd_task_agent_task_delete(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    client.delete_agent_task(task_id=args.task_id)
    return {"deleted": True, "task_id": args.task_id}


def _cmd_task_agent_cycle_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_agent_cycles(
        task_id=args.task_id,
        cycle_index_offset=args.offset,
    )


def _cmd_task_agent_cycle_get(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_agent_cycle(cycle_id=args.cycle_id)


def _cmd_task_agent_agent_create(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    kwargs: dict[str, Any] = {"name": args.name}
    if args.description is not None:
        kwargs["description"] = args.description
    if args.system_prompt is not None:
        kwargs["system_prompt"] = args.system_prompt
    if args.model_name is not None:
        kwargs["default_model_name"] = args.model_name
    if args.backend_type is not None:
        kwargs["default_backend_type"] = args.backend_type
    if args.max_cycles is not None:
        kwargs["default_max_cycles"] = args.max_cycles
    return client.create_agent(**kwargs)


def _cmd_task_agent_agent_update(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    kwargs: dict[str, Any] = {"agent_id": args.agent_id}
    if args.name is not None:
        kwargs["name"] = args.name
    if args.description is not None:
        kwargs["description"] = args.description
    if args.system_prompt is not None:
        kwargs["system_prompt"] = args.system_prompt
    if args.model_name is not None:
        kwargs["default_model_name"] = args.model_name
    if args.backend_type is not None:
        kwargs["default_backend_type"] = args.backend_type
    if args.max_cycles is not None:
        kwargs["default_max_cycles"] = args.max_cycles
    return client.update_agent(**kwargs)


def _cmd_task_agent_agent_delete(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    client.delete_agent(agent_id=args.agent_id)
    return {"deleted": True, "agent_id": args.agent_id}


def _cmd_task_agent_agent_search(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_agents(page=args.page, page_size=args.page_size, search=args.query)


def _cmd_task_agent_task_search(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    status_filter: str | list[str] | None = None
    if args.status:
        status_filter = args.status[0] if len(args.status) == 1 else args.status
    return client.list_agent_tasks(
        page=args.page,
        page_size=args.page_size,
        status=status_filter,
        agent_id=args.agent_id,
        search=args.query,
    )
