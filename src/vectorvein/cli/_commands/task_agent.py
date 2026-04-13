"""Task-agent command handlers for the full task-agent CLI surface."""

from __future__ import annotations

import argparse
from typing import Any

from vectorvein.api import TaskInfo, VectorVeinClient

from vectorvein.cli._output import CLIUsageError
from vectorvein.cli._parsers import (
    _collect_attachments,
    _collect_url_attachments,
    _load_json_array,
    _load_optional_agent_definition,
    _load_optional_agent_settings,
    _load_optional_json_array,
    _load_optional_json_object,
    _load_optional_text_value,
    _load_text_value,
    _poll_task_until_done,
)


def _set_if_not_none(payload: dict[str, Any], key: str, value: Any) -> None:
    if value is not None:
        payload[key] = value


def _load_data_payload(raw: str | None) -> dict[str, Any]:
    return _load_optional_json_object(raw, "--data") or {}


def _load_optional_array(raw: str | None, option_name: str) -> list[Any] | None:
    return _load_optional_json_array(raw, option_name)


def _load_optional_object(raw: str | None, option_name: str) -> dict[str, Any] | None:
    return _load_optional_json_object(raw, option_name)


def _merge_payload(base: dict[str, Any], extra: dict[str, Any] | None) -> dict[str, Any]:
    payload = dict(base)
    if extra:
        payload.update(extra)
    return payload


def _cmd_task_agent_agent_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_agents(
        page=args.page,
        page_size=args.page_size,
        search=args.search,
        is_public=args.is_public,
        official=args.official,
    )


def _cmd_task_agent_agent_get(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_agent(agent_id=args.agent_id)


def _cmd_task_agent_agent_create(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    kwargs: dict[str, Any] = {"name": args.name}
    _set_if_not_none(kwargs, "avatar", args.avatar)
    _set_if_not_none(kwargs, "description", _load_optional_text_value(args.description, "--description"))
    _set_if_not_none(kwargs, "system_prompt", _load_optional_text_value(args.system_prompt, "--system-prompt"))
    _set_if_not_none(kwargs, "usage_hint", _load_optional_object(args.usage_hint, "--usage-hint"))
    _set_if_not_none(kwargs, "default_model_name", args.model_name)
    _set_if_not_none(kwargs, "default_backend_type", args.backend_type)
    _set_if_not_none(kwargs, "default_max_cycles", args.max_cycles)
    _set_if_not_none(kwargs, "default_allow_interruption", args.default_allow_interruption)
    _set_if_not_none(kwargs, "default_use_workspace", args.default_use_workspace)
    _set_if_not_none(kwargs, "default_load_user_memory", args.default_load_user_memory)
    _set_if_not_none(kwargs, "default_compress_memory_after_tokens", args.default_compress_memory_after_tokens)
    _set_if_not_none(kwargs, "default_agent_type", args.default_agent_type)
    _set_if_not_none(kwargs, "default_workspace_files", _load_optional_array(args.default_workspace_files, "--default-workspace-files"))
    _set_if_not_none(kwargs, "default_sub_agent_ids", _load_optional_array(args.default_sub_agent_ids, "--default-sub-agent-ids"))
    _set_if_not_none(kwargs, "required_skills", _load_optional_array(args.required_skills, "--required-skills"))
    _set_if_not_none(kwargs, "default_output_verifier", _load_optional_text_value(args.default_output_verifier, "--default-output-verifier"))
    _set_if_not_none(kwargs, "default_computer_pod_setting_id", args.default_computer_pod_setting_id)
    _set_if_not_none(kwargs, "default_cloud_storage_paths", _load_optional_array(args.default_cloud_storage_paths, "--default-cloud-storage-paths"))
    _set_if_not_none(kwargs, "default_cloud_storage_write_enabled", args.default_cloud_storage_write_enabled)
    _set_if_not_none(kwargs, "available_workflow_ids", _load_optional_array(args.available_workflow_ids, "--available-workflow-ids"))
    _set_if_not_none(kwargs, "available_template_ids", _load_optional_array(args.available_template_ids, "--available-template-ids"))
    _set_if_not_none(kwargs, "available_mcp_tool_ids", _load_optional_array(args.available_mcp_tool_ids, "--available-mcp-tool-ids"))
    _set_if_not_none(kwargs, "tag_ids", _load_optional_array(args.tag_ids, "--tag-ids"))
    _set_if_not_none(kwargs, "shared", args.shared)
    _set_if_not_none(kwargs, "is_public", args.is_public)
    return client.create_agent(**kwargs)


def _cmd_task_agent_agent_update(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    kwargs: dict[str, Any] = {"agent_id": args.agent_id}
    _set_if_not_none(kwargs, "name", args.name)
    _set_if_not_none(kwargs, "avatar", args.avatar)
    _set_if_not_none(kwargs, "description", _load_optional_text_value(args.description, "--description"))
    _set_if_not_none(kwargs, "system_prompt", _load_optional_text_value(args.system_prompt, "--system-prompt"))
    _set_if_not_none(kwargs, "usage_hint", _load_optional_object(args.usage_hint, "--usage-hint"))
    _set_if_not_none(kwargs, "default_model_name", args.model_name)
    _set_if_not_none(kwargs, "default_backend_type", args.backend_type)
    _set_if_not_none(kwargs, "default_max_cycles", args.max_cycles)
    _set_if_not_none(kwargs, "default_allow_interruption", args.default_allow_interruption)
    _set_if_not_none(kwargs, "default_use_workspace", args.default_use_workspace)
    _set_if_not_none(kwargs, "default_load_user_memory", args.default_load_user_memory)
    _set_if_not_none(kwargs, "default_compress_memory_after_tokens", args.default_compress_memory_after_tokens)
    _set_if_not_none(kwargs, "default_agent_type", args.default_agent_type)
    _set_if_not_none(kwargs, "default_workspace_files", _load_optional_array(args.default_workspace_files, "--default-workspace-files"))
    _set_if_not_none(kwargs, "default_sub_agent_ids", _load_optional_array(args.default_sub_agent_ids, "--default-sub-agent-ids"))
    _set_if_not_none(kwargs, "required_skills", _load_optional_array(args.required_skills, "--required-skills"))
    _set_if_not_none(kwargs, "default_output_verifier", _load_optional_text_value(args.default_output_verifier, "--default-output-verifier"))
    _set_if_not_none(kwargs, "default_computer_pod_setting_id", args.default_computer_pod_setting_id)
    _set_if_not_none(kwargs, "default_cloud_storage_paths", _load_optional_array(args.default_cloud_storage_paths, "--default-cloud-storage-paths"))
    _set_if_not_none(kwargs, "default_cloud_storage_write_enabled", args.default_cloud_storage_write_enabled)
    _set_if_not_none(kwargs, "available_workflow_ids", _load_optional_array(args.available_workflow_ids, "--available-workflow-ids"))
    _set_if_not_none(kwargs, "available_template_ids", _load_optional_array(args.available_template_ids, "--available-template-ids"))
    _set_if_not_none(kwargs, "available_mcp_tool_ids", _load_optional_array(args.available_mcp_tool_ids, "--available-mcp-tool-ids"))
    _set_if_not_none(kwargs, "tag_ids", _load_optional_array(args.tag_ids, "--tag-ids"))
    _set_if_not_none(kwargs, "shared", args.shared)
    _set_if_not_none(kwargs, "is_public", args.is_public)
    return client.update_agent(**kwargs)


def _cmd_task_agent_agent_delete(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    client.delete_agent(agent_id=args.agent_id)
    return {"deleted": True, "agent_id": args.agent_id}


def _cmd_task_agent_agent_search(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_agents(
        page=args.page,
        page_size=args.page_size,
        search=args.query,
        is_public=args.is_public,
        official=args.official,
    )


def _cmd_task_agent_agent_favorite_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_favorite_agents(
        page=args.page,
        page_size=args.page_size,
        search=args.search,
        tag_ids=_load_optional_array(args.tag_ids, "--tag-ids"),
    )


def _cmd_task_agent_agent_duplicate(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.duplicate_agent(agent_id=args.agent_id, add_templates=args.add_templates)


def _cmd_task_agent_agent_toggle_favorite(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.toggle_agent_favorite(agent_id=args.agent_id, is_favorited=args.is_favorited)


def _cmd_task_agent_agent_update_system_prompt(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.update_agent_system_prompt(
        agent_id=args.agent_id,
        system_prompt=_load_text_value(args.system_prompt, "--system-prompt"),
        optimization_task_id=args.optimization_task_id,
    )


def _cmd_task_agent_agent_create_optimized(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.create_optimized_agent(
        agent_id=args.agent_id,
        system_prompt=_load_text_value(args.system_prompt, "--system-prompt"),
        name=args.name,
        optimization_task_id=args.optimization_task_id,
    )


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
        raise CLIUsageError(
            "--model-preference custom requires both --custom-backend-type and --custom-model-name.",
            hint="Either provide both custom model fields or switch back to --model-preference default/high_performance/low_cost.",
            example="vectorvein task-agent task create --text 'Do work' --model-preference custom --custom-backend-type openai --custom-model-name gpt-4o",
        )

    task_info = TaskInfo(
        text=_load_text_value(args.text, "--text"),
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
        message=_load_text_value(args.message, "--message"),
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
        message=_load_optional_text_value(args.message, "--message"),
        attachments_detail=_collect_url_attachments(args),
    )
    if not args.wait:
        return result
    return _poll_task_until_done(client, args.task_id, args.timeout)


def _cmd_task_agent_task_respond(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    result = client.respond_to_agent_task(
        task_id=args.task_id,
        tool_call_id=args.tool_call_id,
        response_content=_load_text_value(args.response, "--response"),
    )
    if not args.wait:
        return result
    return _poll_task_until_done(client, args.task_id, args.timeout)


def _cmd_task_agent_task_delete(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    client.delete_agent_task(task_id=args.task_id)
    return {"deleted": True, "task_id": args.task_id}


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


def _cmd_task_agent_task_update_share(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.update_agent_task_share(
        task_id=args.task_id,
        shared=args.shared,
        is_public=args.is_public,
        shared_meta=_load_optional_object(args.shared_meta, "--shared-meta"),
    )


def _cmd_task_agent_task_get_shared(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_shared_agent_task(task_id=args.task_id)


def _cmd_task_agent_task_public_shared_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_public_shared_agent_tasks(
        page=args.page,
        page_size=args.page_size,
        search=args.search,
        sort_field=args.sort_field,
        sort_order=args.sort_order,
    )


def _cmd_task_agent_task_batch_delete(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.batch_delete_agent_tasks(task_ids=_load_json_array(args.task_ids, "--task-ids"))


def _cmd_task_agent_task_add_pending_message(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.add_pending_message(
        task_id=args.task_id,
        message=_load_text_value(args.message, "--message"),
        attachments_detail=_collect_url_attachments(args),
        action_type=args.action_type,
    )


def _cmd_task_agent_task_toggle_hidden(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.toggle_agent_task_hidden(task_id=args.task_id, is_hidden=args.is_hidden)


def _cmd_task_agent_task_toggle_favorite(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.toggle_agent_task_favorite(task_id=args.task_id, is_favorited=args.is_favorited)


def _cmd_task_agent_task_start_prompt_optimization(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.start_prompt_optimization(
        task_id=args.task_id,
        optimization_direction=_load_text_value(args.optimization_direction, "--optimization-direction"),
    )


def _cmd_task_agent_task_prompt_optimizer_config(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_prompt_optimizer_config()


def _cmd_task_agent_task_computer_pod_settings(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_computer_pod_settings()


def _cmd_task_agent_task_close_computer_environment(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.close_computer_environment(task_id=args.task_id)


def _cmd_task_agent_cycle_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_agent_cycles(task_id=args.task_id, cycle_index_offset=args.offset)


def _cmd_task_agent_cycle_get(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_agent_cycle(cycle_id=args.cycle_id)


def _cmd_task_agent_cycle_run_workflow(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.run_agent_cycle_workflow(
        cycle_id=args.cycle_id,
        tool_name=args.tool_name,
        workflow_inputs=_load_optional_object(args.workflow_inputs, "--workflow-inputs"),
    )


def _cmd_task_agent_cycle_check_workflow_status(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.check_agent_cycle_workflow_status(rid=args.rid)


def _cmd_task_agent_cycle_finish_task(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.finish_agent_cycle_task(cycle_id=args.cycle_id, message=_load_text_value(args.message, "--message"))


def _cmd_task_agent_cycle_replay(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.replay_agent_cycles(task_id=args.task_id, start_index=args.start_index, end_index=args.end_index)


def _cmd_task_agent_cycle_replay_summary(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_agent_replay_summary(task_id=args.task_id)


def _cmd_task_agent_tag_create(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.create_agent_tag(title=args.title, color=args.color)


def _cmd_task_agent_tag_delete(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.delete_agent_tag(tag_id=args.tag_id)


def _cmd_task_agent_tag_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "page", args.page)
    _set_if_not_none(payload, "page_size", args.page_size)
    _set_if_not_none(payload, "search", args.search)
    _set_if_not_none(payload, "public_only", args.public_only)
    return client.list_agent_tags(**payload)


def _cmd_task_agent_tag_update(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.update_agent_tags(data=_load_json_array(args.data, "--data"))


def _cmd_task_agent_tag_search(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.search_agent_tags(title=args.title)


def _cmd_task_agent_collection_create(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "title", args.title)
    _set_if_not_none(payload, "description", _load_optional_text_value(args.description, "--description"))
    _set_if_not_none(payload, "agent_ids", _load_optional_array(args.agent_ids, "--agent-ids"))
    _set_if_not_none(payload, "shared", args.shared)
    _set_if_not_none(payload, "is_public", args.is_public)
    return client.create_agent_collection(**payload)


def _cmd_task_agent_collection_get(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_agent_collection(collection_id=args.collection_id)


def _cmd_task_agent_collection_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_agent_collections(page=args.page, page_size=args.page_size, search=args.search)


def _cmd_task_agent_collection_public_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_public_agent_collections(page=args.page, page_size=args.page_size, search=args.search)


def _cmd_task_agent_collection_update(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "title", args.title)
    _set_if_not_none(payload, "description", _load_optional_text_value(args.description, "--description"))
    _set_if_not_none(payload, "agent_ids", _load_optional_array(args.agent_ids, "--agent-ids"))
    _set_if_not_none(payload, "shared", args.shared)
    _set_if_not_none(payload, "is_public", args.is_public)
    return client.update_agent_collection(collection_id=args.collection_id, **payload)


def _cmd_task_agent_collection_delete(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.delete_agent_collection(collection_id=args.collection_id)


def _cmd_task_agent_collection_add_agent(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.add_agent_to_collection(collection_id=args.collection_id, agent_id=args.agent_id)


def _cmd_task_agent_collection_remove_agent(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.remove_agent_from_collection(collection_id=args.collection_id, agent_id=args.agent_id)


def _cmd_task_agent_mcp_server_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "page", args.page)
    _set_if_not_none(payload, "page_size", args.page_size)
    _set_if_not_none(payload, "search", args.search)
    return client.list_mcp_servers(**payload)


def _cmd_task_agent_mcp_server_create(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "name", args.name)
    _set_if_not_none(payload, "description", _load_optional_text_value(args.description, "--description"))
    _set_if_not_none(payload, "server_url", args.server_url)
    _set_if_not_none(payload, "transport_type", args.transport_type)
    _set_if_not_none(payload, "headers", _load_optional_object(args.headers, "--headers"))
    _set_if_not_none(payload, "config", _load_optional_object(args.config, "--config"))
    return client.create_mcp_server(**payload)


def _cmd_task_agent_mcp_server_get(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_mcp_server(server_id=args.server_id)


def _cmd_task_agent_mcp_server_update(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "name", args.name)
    _set_if_not_none(payload, "description", _load_optional_text_value(args.description, "--description"))
    _set_if_not_none(payload, "server_url", args.server_url)
    _set_if_not_none(payload, "transport_type", args.transport_type)
    _set_if_not_none(payload, "headers", _load_optional_object(args.headers, "--headers"))
    _set_if_not_none(payload, "config", _load_optional_object(args.config, "--config"))
    return client.update_mcp_server(server_id=args.server_id, **payload)


def _cmd_task_agent_mcp_server_delete(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.delete_mcp_server(server_id=args.server_id)


def _cmd_task_agent_mcp_server_test_connection(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "server_url", args.server_url)
    _set_if_not_none(payload, "transport_type", args.transport_type)
    _set_if_not_none(payload, "headers", _load_optional_object(args.headers, "--headers"))
    _set_if_not_none(payload, "config", _load_optional_object(args.config, "--config"))
    return client.test_mcp_server_connection(**payload)


def _cmd_task_agent_mcp_server_test_existing(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.test_existing_mcp_server(server_id=args.server_id)


def _cmd_task_agent_mcp_tool_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "page", args.page)
    _set_if_not_none(payload, "page_size", args.page_size)
    _set_if_not_none(payload, "search", args.search)
    _set_if_not_none(payload, "server_id", args.server_id)
    return client.list_mcp_tools(**payload)


def _cmd_task_agent_mcp_tool_create(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "tool_name", args.tool_name)
    _set_if_not_none(payload, "description", _load_optional_text_value(args.description, "--description"))
    _set_if_not_none(payload, "server_id", args.server_id)
    _set_if_not_none(payload, "tool_schema", _load_optional_object(args.tool_schema, "--tool-schema"))
    return client.create_mcp_tool(**payload)


def _cmd_task_agent_mcp_tool_get(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_mcp_tool(tool_id=args.tool_id)


def _cmd_task_agent_mcp_tool_update(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "tool_name", args.tool_name)
    _set_if_not_none(payload, "description", _load_optional_text_value(args.description, "--description"))
    _set_if_not_none(payload, "server_id", args.server_id)
    _set_if_not_none(payload, "tool_schema", _load_optional_object(args.tool_schema, "--tool-schema"))
    return client.update_mcp_tool(tool_id=args.tool_id, **payload)


def _cmd_task_agent_mcp_tool_delete(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.delete_mcp_tool(tool_id=args.tool_id)


def _cmd_task_agent_mcp_tool_logs(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_mcp_tool_logs(tool_id=args.tool_id, page=args.page, page_size=args.page_size)


def _cmd_task_agent_user_memory_create(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "content", _load_optional_text_value(args.content, "--content"))
    _set_if_not_none(payload, "memory_type", args.memory_type)
    _set_if_not_none(payload, "metadata", _load_optional_object(args.metadata, "--metadata"))
    _set_if_not_none(payload, "is_active", args.is_active)
    return client.create_user_memory(**payload)


def _cmd_task_agent_user_memory_get(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_user_memory(memory_id=args.memory_id)


def _cmd_task_agent_user_memory_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_user_memories(
        page=args.page,
        page_size=args.page_size,
        memory_type=args.memory_type,
        is_active=args.is_active,
        search=args.search,
    )


def _cmd_task_agent_user_memory_update(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "content", _load_optional_text_value(args.content, "--content"))
    _set_if_not_none(payload, "memory_type", args.memory_type)
    _set_if_not_none(payload, "metadata", _load_optional_object(args.metadata, "--metadata"))
    _set_if_not_none(payload, "is_active", args.is_active)
    return client.update_user_memory(memory_id=args.memory_id, **payload)


def _cmd_task_agent_user_memory_delete(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.delete_user_memory(memory_id=args.memory_id)


def _cmd_task_agent_user_memory_toggle(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.toggle_user_memory(memory_id=args.memory_id)


def _cmd_task_agent_user_memory_stats(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_user_memory_stats()


def _cmd_task_agent_user_memory_batch_delete(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.batch_delete_user_memories(_load_json_array(args.memory_ids, "--memory-ids"))


def _cmd_task_agent_user_memory_batch_toggle(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.batch_toggle_user_memories(_load_json_array(args.memory_ids, "--memory-ids"), args.is_active)


def _cmd_task_agent_user_memory_types(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_user_memory_types()


def _cmd_task_agent_skill_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "page", args.page)
    _set_if_not_none(payload, "page_size", args.page_size)
    _set_if_not_none(payload, "search", args.search)
    _set_if_not_none(payload, "category_id", args.category_id)
    return client.list_skills(**payload)


def _cmd_task_agent_skill_my_skills(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_my_skills(page=args.page, page_size=args.page_size)


def _cmd_task_agent_skill_get(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_skill(skill_id=args.skill_id)


def _cmd_task_agent_skill_create(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "name", args.name)
    _set_if_not_none(payload, "display_name", args.display_name)
    _set_if_not_none(payload, "description", _load_optional_text_value(args.description, "--description"))
    _set_if_not_none(payload, "content", _load_optional_text_value(args.content, "--content"))
    _set_if_not_none(payload, "category_id", args.category_id)
    _set_if_not_none(payload, "permission_level", args.permission_level)
    _set_if_not_none(payload, "metadata", _load_optional_object(args.metadata, "--metadata"))
    return client.create_skill(**payload)


def _cmd_task_agent_skill_upload_and_parse(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.upload_and_parse_skill(str(args.path), filename=args.filename)


def _cmd_task_agent_skill_update(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "name", args.name)
    _set_if_not_none(payload, "display_name", args.display_name)
    _set_if_not_none(payload, "description", _load_optional_text_value(args.description, "--description"))
    _set_if_not_none(payload, "content", _load_optional_text_value(args.content, "--content"))
    _set_if_not_none(payload, "category_id", args.category_id)
    _set_if_not_none(payload, "permission_level", args.permission_level)
    _set_if_not_none(payload, "metadata", _load_optional_object(args.metadata, "--metadata"))
    return client.update_skill(skill_id=args.skill_id, **payload)


def _cmd_task_agent_skill_delete(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.delete_skill(skill_id=args.skill_id)


def _cmd_task_agent_skill_install(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    kwargs: dict[str, Any] = {"skill_id": args.skill_id}
    _set_if_not_none(kwargs, "agent_id", args.agent_id)
    _set_if_not_none(kwargs, "permission_level", args.permission_level)
    return client.install_skill(**kwargs)


def _cmd_task_agent_skill_uninstall(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.uninstall_skill(skill_id=args.skill_id, agent_id=args.agent_id)


def _cmd_task_agent_skill_installed(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_installed_skills(agent_id=args.agent_id)


def _cmd_task_agent_skill_update_installation(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "is_enabled", args.is_enabled)
    _set_if_not_none(payload, "permission_level", args.permission_level)
    _set_if_not_none(payload, "metadata", _load_optional_object(args.metadata, "--metadata"))
    return client.update_skill_installation(installation_id=args.installation_id, **payload)


def _cmd_task_agent_skill_set_agent_override(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.set_skill_agent_override(skill_id=args.skill_id, agent_id=args.agent_id, is_enabled=args.is_enabled)


def _cmd_task_agent_skill_remove_agent_override(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.remove_skill_agent_override(skill_id=args.skill_id, agent_id=args.agent_id)


def _cmd_task_agent_skill_categories(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_skill_categories()


def _cmd_task_agent_skill_review_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_skill_reviews(skill_id=args.skill_id, page=args.page, page_size=args.page_size)


def _cmd_task_agent_skill_review_create(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.create_skill_review(
        skill_id=args.skill_id,
        rating=args.rating,
        comment=_load_optional_text_value(args.comment, "--comment"),
    )


def _cmd_task_agent_skill_review_delete(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.delete_skill_review(review_id=args.review_id)


def _cmd_task_agent_task_category_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_task_categories()


def _cmd_task_agent_tool_category_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_tool_categories()


def _cmd_task_agent_workflow_tool_official_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "page", args.page)
    _set_if_not_none(payload, "page_size", args.page_size)
    _set_if_not_none(payload, "search", args.search)
    _set_if_not_none(payload, "category_id", args.category_id)
    return client.list_official_workflow_tools(**payload)


def _cmd_task_agent_workflow_tool_my_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "page", args.page)
    _set_if_not_none(payload, "page_size", args.page_size)
    _set_if_not_none(payload, "search", args.search)
    _set_if_not_none(payload, "category_id", args.category_id)
    return client.list_my_workflow_tools(**payload)


def _cmd_task_agent_workflow_tool_create(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "workflow_wid", args.workflow_wid)
    _set_if_not_none(payload, "template_tid", args.template_tid)
    _set_if_not_none(payload, "category_id", args.category_id)
    _set_if_not_none(payload, "display_name", args.display_name)
    _set_if_not_none(payload, "description", _load_optional_text_value(args.description, "--description"))
    return client.create_workflow_tool(**payload)


def _cmd_task_agent_workflow_tool_update(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "workflow_wid", args.workflow_wid)
    _set_if_not_none(payload, "template_tid", args.template_tid)
    _set_if_not_none(payload, "category_id", args.category_id)
    _set_if_not_none(payload, "display_name", args.display_name)
    _set_if_not_none(payload, "description", _load_optional_text_value(args.description, "--description"))
    return client.update_workflow_tool(tool_id=args.tool_id, **payload)


def _cmd_task_agent_workflow_tool_delete(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.delete_workflow_tool(tool_id=args.tool_id)


def _cmd_task_agent_workflow_tool_detail(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_workflow_tool_detail(tool_id=args.tool_id)


def _cmd_task_agent_workflow_tool_batch_create(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    kwargs: dict[str, Any] = {}
    _set_if_not_none(kwargs, "workflow_wids", _load_optional_array(args.workflow_wids, "--workflow-wids"))
    _set_if_not_none(kwargs, "template_tids", _load_optional_array(args.template_tids, "--template-tids"))
    _set_if_not_none(kwargs, "category_id", args.category_id)
    return client.batch_create_workflow_tools(**kwargs)


def _cmd_task_agent_task_schedule_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    payload = _load_data_payload(args.data)
    _set_if_not_none(payload, "page", args.page)
    _set_if_not_none(payload, "page_size", args.page_size)
    _set_if_not_none(payload, "search", args.search)
    _set_if_not_none(payload, "agent_id", args.agent_id)
    _set_if_not_none(payload, "enabled", args.enabled)
    return client.list_task_schedules(**payload)


def _cmd_task_agent_task_schedule_get(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_task_schedule(schedule_id=args.schedule_id)


def _cmd_task_agent_task_schedule_update(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    kwargs: dict[str, Any] = {"cron_expression": args.cron_expression}
    _set_if_not_none(kwargs, "schedule_id", args.schedule_id)
    _set_if_not_none(kwargs, "agent_id", args.agent_id)
    _set_if_not_none(kwargs, "timezone", args.timezone)
    _set_if_not_none(kwargs, "title", args.title)
    _set_if_not_none(kwargs, "task_info", _load_optional_object(args.task_info, "--task-info"))
    _set_if_not_none(kwargs, "mounted_cloud_storage_paths", _load_optional_array(args.mounted_cloud_storage_paths, "--mounted-cloud-storage-paths"))
    _set_if_not_none(kwargs, "max_cycles", args.max_cycles)
    _set_if_not_none(kwargs, "send_email", args.send_email)
    _set_if_not_none(kwargs, "load_user_memory", args.load_user_memory)
    return client.update_task_schedule(**kwargs)


def _cmd_task_agent_task_schedule_delete(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.delete_task_schedule(schedule_id=args.schedule_id)


def _cmd_task_agent_task_schedule_toggle(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.toggle_task_schedule(schedule_id=args.schedule_id, enabled=args.enabled)
