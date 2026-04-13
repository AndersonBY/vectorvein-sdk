"""Task-agent parser builder."""

from __future__ import annotations

import argparse

from vectorvein.cli._builders.common import (
    add_bool_text_argument,
    add_json_data_argument,
    add_paging_arguments,
    add_search_argument,
    rich_parser_kwargs,
)
from vectorvein.cli._commands import task_agent as task_agent_cmd


def _json_array_help(noun: str) -> str:
    return f"JSON array or @file for {noun}."


def _json_object_help(noun: str) -> str:
    return f"JSON object or @file for {noun}."


def _add_agent_create_update_arguments(parser: argparse.ArgumentParser, *, include_agent_id: bool) -> None:
    if include_agent_id:
        basics = parser.add_argument_group("Target Agent")
        basics.add_argument("--agent-id", required=True, help="Agent ID to update.")
    else:
        basics = parser.add_argument_group("Basic Identity")

    if not include_agent_id:
        basics.add_argument("--name", required=True, help="Agent name.")
    else:
        basics.add_argument("--name", help="Agent name.")
    basics.add_argument("--avatar", help="Agent avatar URL.")
    basics.add_argument("--description", help="Agent description.")
    basics.add_argument("--system-prompt", help="System prompt.")
    basics.add_argument("--usage-hint", help=_json_object_help("agent usage_hint metadata"))

    defaults = parser.add_argument_group("Default Runtime")
    defaults.add_argument("--model-name", help="Default model name.")
    defaults.add_argument("--backend-type", help="Default backend type.")
    defaults.add_argument("--max-cycles", type=int, help="Default max cycles.")
    add_bool_text_argument(defaults, "--default-allow-interruption", help_text="Whether the agent allows interruption by default.")
    add_bool_text_argument(defaults, "--default-use-workspace", help_text="Whether the agent uses a workspace by default.")
    add_bool_text_argument(defaults, "--default-load-user-memory", help_text="Whether the agent loads user memory by default.")
    defaults.add_argument("--default-compress-memory-after-tokens", type=int, help="Compress memory threshold in tokens.")
    defaults.add_argument("--default-agent-type", help="Default agent type, for example tool or computer.")

    workspace = parser.add_argument_group("Workspace and Skills")
    workspace.add_argument("--default-workspace-files", help=_json_array_help("default workspace file descriptors"))
    workspace.add_argument("--default-sub-agent-ids", help=_json_array_help("default sub-agent IDs"))
    workspace.add_argument("--required-skills", help=_json_array_help("required skill definitions"))
    workspace.add_argument("--default-output-verifier", help="Default output verifier script.")
    workspace.add_argument("--default-computer-pod-setting-id", help="Default computer pod setting ID.")

    resources = parser.add_argument_group("Mounted Resources")
    resources.add_argument("--default-cloud-storage-paths", help=_json_array_help("mounted cloud storage paths"))
    add_bool_text_argument(resources, "--default-cloud-storage-write-enabled", help_text="Whether mounted cloud storage is writable.")
    resources.add_argument("--available-workflow-ids", help=_json_array_help("available workflow IDs"))
    resources.add_argument("--available-template-ids", help=_json_array_help("available template IDs"))
    resources.add_argument("--available-mcp-tool-ids", help=_json_array_help("available MCP tool IDs"))
    resources.add_argument("--tag-ids", help=_json_array_help("agent tag IDs"))

    sharing = parser.add_argument_group("Visibility")
    add_bool_text_argument(sharing, "--shared", help_text="Whether the agent is shared.")
    add_bool_text_argument(sharing, "--is-public", help_text="Whether the agent is publicly visible.")
    add_bool_text_argument(sharing, "--is-official", help_text="Whether the agent is marked as official.")
    sharing.add_argument("--official-order", type=int, help="Official ordering priority.")


def _add_attachment_arguments(parser: argparse.ArgumentParser, *, allow_oss_key: bool) -> None:
    help_suffix = (
        "Single attachment JSON object with exactly one of {url, oss_key}. Repeat for multiple."
        if allow_oss_key
        else "Single attachment JSON object with a URL attachment. Repeat for multiple."
    )
    parser.add_argument("--attachment", action="append", default=[], help=help_suffix)
    parser.add_argument("--attachments", help="JSON array or @file for attachments.")


def _register_agent_group(task_agent_sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    agent_parser = task_agent_sub.add_parser(
        "agent",
        help="Create, inspect, update, duplicate, and favorite reusable agents.",
        **rich_parser_kwargs(
            "Manage reusable task-agent definitions, favorites, duplication, and optimization helpers.",
            examples=[
                "vectorvein task-agent agent list",
                "vectorvein task-agent agent create --name 'Research Assistant'",
                "vectorvein task-agent agent duplicate --agent-id agent_xxx",
            ],
            notes=[
                "--usage-hint accepts a JSON object or @file.",
                "Array-style fields such as --default-sub-agent-ids accept inline JSON arrays or @file.",
            ],
        ),
    )
    agent_sub = agent_parser.add_subparsers(dest="task_agent_agent_command")
    agent_sub.required = True

    agent_list = agent_sub.add_parser(
        "list", help="List saved agents.", **rich_parser_kwargs("List agents visible to the current account.", examples=["vectorvein task-agent agent list --search research"])
    )
    add_paging_arguments(agent_list)
    add_search_argument(agent_list)
    agent_list.set_defaults(handler=task_agent_cmd._cmd_task_agent_agent_list, command="task-agent agent list")

    agent_get = agent_sub.add_parser(
        "get", help="Get one saved agent by ID.", **rich_parser_kwargs("Fetch one agent by ID.", examples=["vectorvein task-agent agent get --agent-id agent_xxx"])
    )
    agent_get.add_argument("--agent-id", required=True, help="Agent ID.")
    agent_get.set_defaults(handler=task_agent_cmd._cmd_task_agent_agent_get, command="task-agent agent get")

    agent_create = agent_sub.add_parser(
        "create",
        help="Create a reusable agent with the full current schema.",
        **rich_parser_kwargs(
            "Create a new saved agent using the latest backend-aligned task-agent schema.",
            examples=[
                "vectorvein task-agent agent create --name 'Research Assistant' --model-name gpt-4o --backend-type openai",
                "vectorvein task-agent agent create --name 'Computer Agent' --default-agent-type computer --default-compress-memory-after-tokens 64000",
            ],
            notes=[
                "--usage-hint must be a JSON object.",
                "List-style fields accept inline JSON arrays or @file.",
                "Use --default-compress-memory-after-tokens; the old *_after_characters field is not supported.",
            ],
        ),
    )
    _add_agent_create_update_arguments(agent_create, include_agent_id=False)
    agent_create.set_defaults(handler=task_agent_cmd._cmd_task_agent_agent_create, command="task-agent agent create")

    agent_update = agent_sub.add_parser(
        "update",
        help="Update an existing saved agent.",
        **rich_parser_kwargs(
            "Update selected fields on a saved agent. Only provided options are changed.",
            examples=["vectorvein task-agent agent update --agent-id agent_xxx --default-load-user-memory false --tag-ids '[\"tag_1\"]'"],
            notes=["All list-style fields accept inline JSON arrays or @file."],
        ),
    )
    _add_agent_create_update_arguments(agent_update, include_agent_id=True)
    agent_update.set_defaults(handler=task_agent_cmd._cmd_task_agent_agent_update, command="task-agent agent update")

    agent_delete = agent_sub.add_parser(
        "delete", help="Delete a saved agent.", **rich_parser_kwargs("Delete a saved agent by ID.", examples=["vectorvein task-agent agent delete --agent-id agent_xxx"])
    )
    agent_delete.add_argument("--agent-id", required=True, help="Agent ID.")
    agent_delete.set_defaults(handler=task_agent_cmd._cmd_task_agent_agent_delete, command="task-agent agent delete")

    agent_search = agent_sub.add_parser(
        "search", help="Search saved agents by keyword.", **rich_parser_kwargs("Search saved agents by keyword.", examples=["vectorvein task-agent agent search --query research"])
    )
    agent_search.add_argument("--query", required=True, help="Search keyword.")
    add_paging_arguments(agent_search)
    agent_search.set_defaults(handler=task_agent_cmd._cmd_task_agent_agent_search, command="task-agent agent search")

    agent_public_list = agent_sub.add_parser(
        "public-list",
        help="List public agents.",
        **rich_parser_kwargs("List public agents, optionally limited to official entries.", examples=["vectorvein task-agent agent public-list --official true"]),
    )
    add_paging_arguments(agent_public_list)
    add_search_argument(agent_public_list)
    add_bool_text_argument(agent_public_list, "--official", help_text="Filter to official agents only.")
    agent_public_list.set_defaults(handler=task_agent_cmd._cmd_task_agent_agent_public_list, command="task-agent agent public-list")

    agent_favorite_list = agent_sub.add_parser(
        "favorite-list",
        help="List favorited agents.",
        **rich_parser_kwargs("List the current user's favorited agents.", examples=["vectorvein task-agent agent favorite-list --tag-ids '[\"tag_1\"]'"]),
    )
    add_paging_arguments(agent_favorite_list)
    add_search_argument(agent_favorite_list)
    agent_favorite_list.add_argument("--tag-ids", help=_json_array_help("favorite tag IDs"))
    agent_favorite_list.set_defaults(handler=task_agent_cmd._cmd_task_agent_agent_favorite_list, command="task-agent agent favorite-list")

    agent_duplicate = agent_sub.add_parser(
        "duplicate",
        help="Duplicate an agent into your account.",
        **rich_parser_kwargs("Duplicate a saved agent.", examples=["vectorvein task-agent agent duplicate --agent-id agent_xxx --add-templates true"]),
    )
    agent_duplicate.add_argument("--agent-id", required=True, help="Source agent ID.")
    add_bool_text_argument(agent_duplicate, "--add-templates", help_text="Whether to add related templates during duplication.")
    agent_duplicate.set_defaults(handler=task_agent_cmd._cmd_task_agent_agent_duplicate, command="task-agent agent duplicate")

    agent_toggle_favorite = agent_sub.add_parser(
        "toggle-favorite",
        help="Favorite or unfavorite an agent.",
        **rich_parser_kwargs("Toggle an agent favorite status.", examples=["vectorvein task-agent agent toggle-favorite --agent-id agent_xxx --is-favorited true"]),
    )
    agent_toggle_favorite.add_argument("--agent-id", required=True, help="Agent ID.")
    add_bool_text_argument(agent_toggle_favorite, "--is-favorited", help_text="Target favorite state.")
    agent_toggle_favorite.set_defaults(handler=task_agent_cmd._cmd_task_agent_agent_toggle_favorite, command="task-agent agent toggle-favorite")

    agent_update_prompt = agent_sub.add_parser(
        "update-system-prompt",
        help="Update only the agent system prompt.",
        **rich_parser_kwargs(
            "Update a saved agent's system prompt, optionally linked to a prompt optimization task.",
            examples=["vectorvein task-agent agent update-system-prompt --agent-id agent_xxx --system-prompt 'You are precise.'"],
        ),
    )
    agent_update_prompt.add_argument("--agent-id", required=True, help="Agent ID.")
    agent_update_prompt.add_argument("--system-prompt", required=True, help="New system prompt.")
    agent_update_prompt.add_argument("--optimization-task-id", help="Prompt optimization task ID.")
    agent_update_prompt.set_defaults(handler=task_agent_cmd._cmd_task_agent_agent_update_system_prompt, command="task-agent agent update-system-prompt")

    agent_create_optimized = agent_sub.add_parser(
        "create-optimized",
        help="Create a new agent from optimized prompt output.",
        **rich_parser_kwargs(
            "Create a new optimized agent derived from an existing one.",
            examples=["vectorvein task-agent agent create-optimized --agent-id agent_xxx --system-prompt 'Improved prompt' --name 'Optimized Assistant'"],
        ),
    )
    agent_create_optimized.add_argument("--agent-id", required=True, help="Source agent ID.")
    agent_create_optimized.add_argument("--system-prompt", required=True, help="Optimized system prompt.")
    agent_create_optimized.add_argument("--name", help="New optimized agent name.")
    agent_create_optimized.add_argument("--optimization-task-id", help="Prompt optimization task ID.")
    agent_create_optimized.set_defaults(handler=task_agent_cmd._cmd_task_agent_agent_create_optimized, command="task-agent agent create-optimized")


def _register_task_group(task_agent_sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    task_parser = task_agent_sub.add_parser(
        "task",
        help="Create, inspect, control, and share agent tasks.",
        **rich_parser_kwargs(
            "Run agents, continue paused tasks, answer waiting questions, and manage shared task results.",
            examples=[
                "vectorvein task-agent task create --agent-id agent_xxx --text 'Summarize this article' --wait",
                "vectorvein task-agent task respond --task-id task_xxx --tool-call-id tc_xxx --response 'Yes, proceed'",
                "vectorvein task-agent task update-share --task-id task_xxx --shared true --is-public false",
            ],
            notes=[
                "--agent-definition and --agent-settings accept JSON objects or @file.",
                "Use compress_memory_after_tokens in task-agent JSON schemas.",
            ],
        ),
    )
    task_sub = task_parser.add_subparsers(dest="task_agent_task_command")
    task_sub.required = True

    task_list = task_sub.add_parser(
        "list", help="List agent tasks.", **rich_parser_kwargs("List agent tasks.", examples=["vectorvein task-agent task list --status completed --agent-id agent_xxx"])
    )
    add_paging_arguments(task_list)
    task_list.add_argument("--status", action="append", help="Task status filter. Repeat to pass multiple values.")
    task_list.add_argument("--agent-id", help="Filter tasks by agent ID.")
    add_search_argument(task_list)
    task_list.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_list, command="task-agent task list")

    task_get = task_sub.add_parser(
        "get", help="Get one task by ID.", **rich_parser_kwargs("Fetch one agent task by task ID.", examples=["vectorvein task-agent task get --task-id task_xxx"])
    )
    task_get.add_argument("--task-id", required=True, help="Task ID.")
    task_get.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_get, command="task-agent task get")

    task_create = task_sub.add_parser(
        "create",
        help="Create an agent task from a saved agent or ad-hoc agent definition.",
        **rich_parser_kwargs(
            """
            Create an agent task.
            Use --agent-id to start from a saved agent, or --agent-definition for an ad-hoc agent configuration.
            """,
            examples=[
                "vectorvein task-agent task create --agent-id agent_xxx --text 'Summarize this report' --wait",
                "vectorvein task-agent task create --text 'Do work' --agent-definition @agent-definition.json",
            ],
            notes=[
                "--attachment accepts JSON objects with exactly one of {url, oss_key}.",
                '--agent-definition example: {"model_name":"gpt-4o","backend_type":"openai","compress_memory_after_tokens":64000}',
                '--agent-settings example: {"model_name":"gpt-4o","backend_type":"openai","compress_memory_after_tokens":64000}',
            ],
            fixes=[
                "If you use --model-preference custom, also provide --custom-backend-type and --custom-model-name.",
                "Use token-based memory thresholds in task-agent JSON schemas.",
            ],
        ),
    )
    task_create.add_argument("--text", required=True, help="Task instruction text.")
    task_create.add_argument("--agent-id", help="Saved agent ID to start.")
    task_create.add_argument("--title", help="Optional task title.")
    task_create.add_argument("--max-cycles", type=int, help="Override max cycles.")
    task_create.add_argument("--model-preference", choices=("default", "high_performance", "low_cost", "custom"), default="default", help="Model preference (default: default).")
    task_create.add_argument("--custom-backend-type", help="Required when --model-preference is custom.")
    task_create.add_argument("--custom-model-name", help="Required when --model-preference is custom.")
    _add_attachment_arguments(task_create, allow_oss_key=True)
    task_create.add_argument("--agent-definition", help=_json_object_help("AgentDefinition"))
    task_create.add_argument("--agent-settings", help=_json_object_help("AgentSettings"))
    task_create.add_argument("--wait", action="store_true", help="Wait until the task finishes, fails, or asks a question.")
    task_create.add_argument("--timeout", type=int, default=600, help="Timeout in seconds when --wait is set (default: 600).")
    task_create.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_create, command="task-agent task create")

    task_continue = task_sub.add_parser(
        "continue",
        help="Continue an existing task with a new message.",
        **rich_parser_kwargs(
            "Continue an existing task with a follow-up instruction.",
            examples=["vectorvein task-agent task continue --task-id task_xxx --message 'Please refine the answer.' --wait"],
        ),
    )
    task_continue.add_argument("--task-id", required=True, help="Task ID.")
    task_continue.add_argument("--message", required=True, help="Follow-up message.")
    _add_attachment_arguments(task_continue, allow_oss_key=False)
    task_continue.add_argument("--wait", action="store_true", help="Wait until the task finishes, fails, or asks another question.")
    task_continue.add_argument("--timeout", type=int, default=600, help="Timeout in seconds when --wait is set (default: 600).")
    task_continue.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_continue, command="task-agent task continue")

    task_pause = task_sub.add_parser(
        "pause", help="Pause a running task.", **rich_parser_kwargs("Pause a running task.", examples=["vectorvein task-agent task pause --task-id task_xxx"])
    )
    task_pause.add_argument("--task-id", required=True, help="Task ID.")
    task_pause.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_pause, command="task-agent task pause")

    task_resume = task_sub.add_parser(
        "resume",
        help="Resume a paused task.",
        **rich_parser_kwargs(
            "Resume a paused task, optionally with a message.",
            examples=["vectorvein task-agent task resume --task-id task_xxx --message 'Continue from the previous plan.' --wait"],
        ),
    )
    task_resume.add_argument("--task-id", required=True, help="Task ID.")
    task_resume.add_argument("--message", help="Optional resume message.")
    _add_attachment_arguments(task_resume, allow_oss_key=False)
    task_resume.add_argument("--wait", action="store_true", help="Wait until the task finishes, fails, or asks another question.")
    task_resume.add_argument("--timeout", type=int, default=600, help="Timeout in seconds when --wait is set (default: 600).")
    task_resume.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_resume, command="task-agent task resume")

    task_respond = task_sub.add_parser(
        "respond",
        help="Respond to a waiting task question.",
        **rich_parser_kwargs(
            "Answer a task that is waiting for human input.",
            examples=["vectorvein task-agent task respond --task-id task_xxx --tool-call-id tc_xxx --response 'Proceed with step 2.' --wait"],
        ),
    )
    task_respond.add_argument("--task-id", required=True, help="Task ID.")
    task_respond.add_argument("--tool-call-id", required=True, help="Tool call ID from waiting_question.")
    task_respond.add_argument("--response", required=True, help="Human response content.")
    task_respond.add_argument("--wait", action="store_true", help="Wait until the task finishes, fails, or asks another question.")
    task_respond.add_argument("--timeout", type=int, default=600, help="Timeout in seconds when --wait is set (default: 600).")
    task_respond.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_respond, command="task-agent task respond")

    task_delete = task_sub.add_parser(
        "delete", help="Delete a task.", **rich_parser_kwargs("Delete a task by task ID.", examples=["vectorvein task-agent task delete --task-id task_xxx"])
    )
    task_delete.add_argument("--task-id", required=True, help="Task ID.")
    task_delete.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_delete, command="task-agent task delete")

    task_search = task_sub.add_parser(
        "search", help="Search tasks by keyword.", **rich_parser_kwargs("Search agent tasks by keyword.", examples=["vectorvein task-agent task search --query summary"])
    )
    task_search.add_argument("--query", required=True, help="Search keyword.")
    add_paging_arguments(task_search)
    task_search.add_argument("--status", action="append", help="Task status filter. Repeat for multiple values.")
    task_search.add_argument("--agent-id", help="Filter by agent ID.")
    task_search.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_search, command="task-agent task search")

    task_update_share = task_sub.add_parser(
        "update-share",
        help="Update task sharing metadata.",
        **rich_parser_kwargs(
            "Update whether a task is shared or public and optionally attach share metadata.",
            examples=["vectorvein task-agent task update-share --task-id task_xxx --shared true --shared-meta @share-meta.json"],
        ),
    )
    task_update_share.add_argument("--task-id", required=True, help="Task ID.")
    add_bool_text_argument(task_update_share, "--shared", help_text="Whether the task is shared.")
    add_bool_text_argument(task_update_share, "--is-public", help_text="Whether the shared task is public.")
    task_update_share.add_argument("--shared-meta", help=_json_object_help("shared_meta"))
    task_update_share.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_update_share, command="task-agent task update-share")

    task_get_shared = task_sub.add_parser(
        "get-shared", help="Get a shared task.", **rich_parser_kwargs("Fetch a shared task by task ID.", examples=["vectorvein task-agent task get-shared --task-id task_xxx"])
    )
    task_get_shared.add_argument("--task-id", required=True, help="Task ID.")
    task_get_shared.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_get_shared, command="task-agent task get-shared")

    task_public_shared_list = task_sub.add_parser(
        "public-shared-list",
        help="List public shared tasks.",
        **rich_parser_kwargs("List public shared tasks.", examples=["vectorvein task-agent task public-shared-list --search design"]),
    )
    add_paging_arguments(task_public_shared_list)
    add_search_argument(task_public_shared_list)
    task_public_shared_list.add_argument("--sort-field", default="update_time", help="Sort field (default: update_time).")
    task_public_shared_list.add_argument("--sort-order", choices=("ascend", "descend"), default="descend", help="Sort order (default: descend).")
    task_public_shared_list.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_public_shared_list, command="task-agent task public-shared-list")

    task_batch_delete = task_sub.add_parser(
        "batch-delete",
        help="Delete multiple tasks at once.",
        **rich_parser_kwargs("Delete multiple tasks with one request.", examples=['vectorvein task-agent task batch-delete --task-ids \'["task_1","task_2"]\'']),
    )
    task_batch_delete.add_argument("--task-ids", required=True, help=_json_array_help("task IDs"))
    task_batch_delete.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_batch_delete, command="task-agent task batch-delete")

    task_add_pending = task_sub.add_parser(
        "add-pending-message",
        help="Queue a pending human message for a task.",
        **rich_parser_kwargs(
            "Attach a pending human message to a task.", examples=["vectorvein task-agent task add-pending-message --task-id task_xxx --message 'Use the latest pricing sheet.'"]
        ),
    )
    task_add_pending.add_argument("--task-id", required=True, help="Task ID.")
    task_add_pending.add_argument("--message", required=True, help="Pending human message.")
    task_add_pending.add_argument("--action-type", help="Optional action type label.")
    _add_attachment_arguments(task_add_pending, allow_oss_key=False)
    task_add_pending.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_add_pending_message, command="task-agent task add-pending-message")

    task_toggle_hidden = task_sub.add_parser(
        "toggle-hidden",
        help="Hide or unhide a task.",
        **rich_parser_kwargs("Toggle whether a task is hidden in list views.", examples=["vectorvein task-agent task toggle-hidden --task-id task_xxx --is-hidden true"]),
    )
    task_toggle_hidden.add_argument("--task-id", required=True, help="Task ID.")
    add_bool_text_argument(task_toggle_hidden, "--is-hidden", help_text="Target hidden state.")
    task_toggle_hidden.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_toggle_hidden, command="task-agent task toggle-hidden")

    task_toggle_favorite = task_sub.add_parser(
        "toggle-favorite",
        help="Favorite or unfavorite a task.",
        **rich_parser_kwargs("Toggle whether a task is favorited.", examples=["vectorvein task-agent task toggle-favorite --task-id task_xxx --is-favorited true"]),
    )
    task_toggle_favorite.add_argument("--task-id", required=True, help="Task ID.")
    add_bool_text_argument(task_toggle_favorite, "--is-favorited", help_text="Target favorite state.")
    task_toggle_favorite.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_toggle_favorite, command="task-agent task toggle-favorite")

    task_prompt_opt = task_sub.add_parser(
        "start-prompt-optimization",
        help="Start prompt optimization for a task.",
        **rich_parser_kwargs(
            "Start prompt optimization for the task's source agent or execution.",
            examples=["vectorvein task-agent task start-prompt-optimization --task-id task_xxx --optimization-direction 'make reasoning more concise'"],
        ),
    )
    task_prompt_opt.add_argument("--task-id", required=True, help="Task ID.")
    task_prompt_opt.add_argument("--optimization-direction", required=True, help="Prompt optimization goal or direction.")
    task_prompt_opt.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_start_prompt_optimization, command="task-agent task start-prompt-optimization")

    task_prompt_config = task_sub.add_parser(
        "prompt-optimizer-config",
        help="Get prompt optimizer configuration.",
        **rich_parser_kwargs("Fetch prompt optimizer configuration.", examples=["vectorvein task-agent task prompt-optimizer-config"]),
    )
    task_prompt_config.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_prompt_optimizer_config, command="task-agent task prompt-optimizer-config")

    task_pod_settings = task_sub.add_parser(
        "computer-pod-settings",
        help="List computer pod settings.",
        **rich_parser_kwargs("List available computer pod settings for computer-type agents.", examples=["vectorvein task-agent task computer-pod-settings"]),
    )
    task_pod_settings.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_computer_pod_settings, command="task-agent task computer-pod-settings")

    task_close_computer = task_sub.add_parser(
        "close-computer-environment",
        help="Close a task's computer environment.",
        **rich_parser_kwargs("Close the computer environment associated with a task.", examples=["vectorvein task-agent task close-computer-environment --task-id task_xxx"]),
    )
    task_close_computer.add_argument("--task-id", required=True, help="Task ID.")
    task_close_computer.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_close_computer_environment, command="task-agent task close-computer-environment")


def _register_cycle_group(task_agent_sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    cycle_parser = task_agent_sub.add_parser(
        "cycle",
        help="Inspect cycles, replay reasoning, and run cycle workflows.",
        **rich_parser_kwargs(
            "Inspect reasoning cycles, run tool workflows, replay execution history, and mark cycle tasks as finished.",
            examples=[
                "vectorvein task-agent cycle list --task-id task_xxx",
                "vectorvein task-agent cycle run-workflow --cycle-id cycle_xxx --tool-name summarize --workflow-inputs @inputs.json",
            ],
        ),
    )
    cycle_sub = cycle_parser.add_subparsers(dest="task_agent_cycle_command")
    cycle_sub.required = True

    cycle_list = cycle_sub.add_parser(
        "list",
        help="List cycles for a task.",
        **rich_parser_kwargs("List reasoning cycles for a task.", examples=["vectorvein task-agent cycle list --task-id task_xxx --offset 0"]),
    )
    cycle_list.add_argument("--task-id", required=True, help="Task ID.")
    cycle_list.add_argument("--offset", type=int, default=0, help="Cycle index offset (default: 0).")
    cycle_list.set_defaults(handler=task_agent_cmd._cmd_task_agent_cycle_list, command="task-agent cycle list")

    cycle_get = cycle_sub.add_parser(
        "get", help="Get one cycle by ID.", **rich_parser_kwargs("Fetch one reasoning cycle by cycle ID.", examples=["vectorvein task-agent cycle get --cycle-id cycle_xxx"])
    )
    cycle_get.add_argument("--cycle-id", required=True, help="Cycle ID.")
    cycle_get.set_defaults(handler=task_agent_cmd._cmd_task_agent_cycle_get, command="task-agent cycle get")

    cycle_run_workflow = cycle_sub.add_parser(
        "run-workflow",
        help="Run a workflow tool from a cycle.",
        **rich_parser_kwargs(
            "Trigger a workflow tool call for a cycle.",
            examples=["vectorvein task-agent cycle run-workflow --cycle-id cycle_xxx --tool-name search --workflow-inputs @inputs.json"],
            notes=["--workflow-inputs accepts a JSON object or @file."],
        ),
    )
    cycle_run_workflow.add_argument("--cycle-id", required=True, help="Cycle ID.")
    cycle_run_workflow.add_argument("--tool-name", required=True, help="Tool name.")
    cycle_run_workflow.add_argument("--workflow-inputs", help=_json_object_help("workflow input payload"))
    cycle_run_workflow.set_defaults(handler=task_agent_cmd._cmd_task_agent_cycle_run_workflow, command="task-agent cycle run-workflow")

    cycle_check = cycle_sub.add_parser(
        "check-workflow-status",
        help="Check cycle workflow execution status.",
        **rich_parser_kwargs("Check status for a workflow triggered from a task-agent cycle.", examples=["vectorvein task-agent cycle check-workflow-status --rid rid_xxx"]),
    )
    cycle_check.add_argument("--rid", required=True, help="Workflow run record ID.")
    cycle_check.set_defaults(handler=task_agent_cmd._cmd_task_agent_cycle_check_workflow_status, command="task-agent cycle check-workflow-status")

    cycle_finish = cycle_sub.add_parser(
        "finish-task",
        help="Mark a cycle task as finished.",
        **rich_parser_kwargs(
            "Mark a task-agent cycle task as finished with a final message.", examples=["vectorvein task-agent cycle finish-task --cycle-id cycle_xxx --message done"]
        ),
    )
    cycle_finish.add_argument("--cycle-id", required=True, help="Cycle ID.")
    cycle_finish.add_argument("--message", default="任务已完成", help="Finish message (default: 任务已完成).")
    cycle_finish.set_defaults(handler=task_agent_cmd._cmd_task_agent_cycle_finish_task, command="task-agent cycle finish-task")

    cycle_replay = cycle_sub.add_parser(
        "replay",
        help="Replay a task's cycles.",
        **rich_parser_kwargs(
            "Replay cycles for a task over a chosen index range.", examples=["vectorvein task-agent cycle replay --task-id task_xxx --start-index 0 --end-index 5"]
        ),
    )
    cycle_replay.add_argument("--task-id", required=True, help="Task ID.")
    cycle_replay.add_argument("--start-index", type=int, default=0, help="Replay start cycle index (default: 0).")
    cycle_replay.add_argument("--end-index", type=int, help="Replay end cycle index.")
    cycle_replay.set_defaults(handler=task_agent_cmd._cmd_task_agent_cycle_replay, command="task-agent cycle replay")

    cycle_replay_summary = cycle_sub.add_parser(
        "replay-summary",
        help="Get replay summary for a task.",
        **rich_parser_kwargs("Fetch replay summary statistics for a task.", examples=["vectorvein task-agent cycle replay-summary --task-id task_xxx"]),
    )
    cycle_replay_summary.add_argument("--task-id", required=True, help="Task ID.")
    cycle_replay_summary.set_defaults(handler=task_agent_cmd._cmd_task_agent_cycle_replay_summary, command="task-agent cycle replay-summary")


def _register_tag_group(task_agent_sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    tag_parser = task_agent_sub.add_parser(
        "tag",
        help="Create, search, and maintain agent tags.",
        **rich_parser_kwargs("Manage task-agent tags.", examples=["vectorvein task-agent tag create --title Office --color '#3366ff'"]),
    )
    tag_sub = tag_parser.add_subparsers(dest="task_agent_tag_command")
    tag_sub.required = True

    tag_create = tag_sub.add_parser(
        "create", help="Create a tag.", **rich_parser_kwargs("Create an agent tag.", examples=["vectorvein task-agent tag create --title Office --color '#3366ff'"])
    )
    tag_create.add_argument("--title", required=True, help="Tag title.")
    tag_create.add_argument("--color", help="Tag color string.")
    tag_create.set_defaults(handler=task_agent_cmd._cmd_task_agent_tag_create, command="task-agent tag create")

    tag_delete = tag_sub.add_parser(
        "delete", help="Delete a tag.", **rich_parser_kwargs("Delete an agent tag by ID.", examples=["vectorvein task-agent tag delete --tag-id tag_xxx"])
    )
    tag_delete.add_argument("--tag-id", required=True, help="Tag ID.")
    tag_delete.set_defaults(handler=task_agent_cmd._cmd_task_agent_tag_delete, command="task-agent tag delete")

    tag_list = tag_sub.add_parser(
        "list",
        help="List tags.",
        **rich_parser_kwargs(
            "List task-agent tags.", examples=["vectorvein task-agent tag list --public-only true"], notes=["--data accepts extra list filters as a JSON object or @file."]
        ),
    )
    add_paging_arguments(tag_list)
    add_search_argument(tag_list)
    add_bool_text_argument(tag_list, "--public-only", help_text="Whether to limit results to public tags.")
    add_json_data_argument(tag_list)
    tag_list.set_defaults(handler=task_agent_cmd._cmd_task_agent_tag_list, command="task-agent tag list")

    tag_update = tag_sub.add_parser(
        "update",
        help="Batch update tags.",
        **rich_parser_kwargs(
            "Batch update tags using a JSON array payload.", examples=["vectorvein task-agent tag update --data @tags.json"], notes=["--data must be a JSON array of tag objects."]
        ),
    )
    tag_update.add_argument("--data", required=True, help="JSON array or @file containing tag update objects.")
    tag_update.set_defaults(handler=task_agent_cmd._cmd_task_agent_tag_update, command="task-agent tag update")

    tag_search = tag_sub.add_parser(
        "search", help="Search tags by title.", **rich_parser_kwargs("Search agent tags by title.", examples=["vectorvein task-agent tag search --title Office"])
    )
    tag_search.add_argument("--title", required=True, help="Tag title keyword.")
    tag_search.set_defaults(handler=task_agent_cmd._cmd_task_agent_tag_search, command="task-agent tag search")


def _register_collection_group(task_agent_sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    collection_parser = task_agent_sub.add_parser(
        "collection",
        help="Organize agents into reusable collections.",
        **rich_parser_kwargs("Manage reusable collections of agents.", examples=["vectorvein task-agent collection create --title 'Ops Team' --agent-ids '[\"agent_1\"]'"]),
    )
    collection_sub = collection_parser.add_subparsers(dest="task_agent_collection_command")
    collection_sub.required = True

    for name, help_text, handler, command in [
        ("get", "Get one collection by ID.", task_agent_cmd._cmd_task_agent_collection_get, "task-agent collection get"),
        ("delete", "Delete a collection.", task_agent_cmd._cmd_task_agent_collection_delete, "task-agent collection delete"),
    ]:
        parser = collection_sub.add_parser(name, help=help_text, **rich_parser_kwargs(help_text, examples=[f"vectorvein {command} --collection-id collection_xxx"]))
        parser.add_argument("--collection-id", required=True, help="Collection ID.")
        parser.set_defaults(handler=handler, command=command)

    collection_create = collection_sub.add_parser(
        "create",
        help="Create a collection.",
        **rich_parser_kwargs(
            "Create a reusable agent collection.",
            examples=["vectorvein task-agent collection create --title 'Docs Agents' --description 'Knowledge assistants' --data @collection.json"],
        ),
    )
    collection_create.add_argument("--title", help="Collection title.")
    collection_create.add_argument("--description", help="Collection description.")
    collection_create.add_argument("--agent-ids", help=_json_array_help("agent IDs"))
    add_bool_text_argument(collection_create, "--shared", help_text="Whether the collection is shared.")
    add_bool_text_argument(collection_create, "--is-public", help_text="Whether the collection is public.")
    add_json_data_argument(collection_create)
    collection_create.set_defaults(handler=task_agent_cmd._cmd_task_agent_collection_create, command="task-agent collection create")

    collection_list = collection_sub.add_parser(
        "list", help="List your collections.", **rich_parser_kwargs("List your agent collections.", examples=["vectorvein task-agent collection list --search docs"])
    )
    add_paging_arguments(collection_list)
    add_search_argument(collection_list)
    collection_list.set_defaults(handler=task_agent_cmd._cmd_task_agent_collection_list, command="task-agent collection list")

    collection_public_list = collection_sub.add_parser(
        "public-list",
        help="List public collections.",
        **rich_parser_kwargs("List public agent collections.", examples=["vectorvein task-agent collection public-list --search docs"]),
    )
    add_paging_arguments(collection_public_list)
    add_search_argument(collection_public_list)
    collection_public_list.set_defaults(handler=task_agent_cmd._cmd_task_agent_collection_public_list, command="task-agent collection public-list")

    collection_update = collection_sub.add_parser(
        "update",
        help="Update a collection.",
        **rich_parser_kwargs(
            "Update a collection using explicit flags or --data.", examples=["vectorvein task-agent collection update --collection-id collection_xxx --title 'Updated Title'"]
        ),
    )
    collection_update.add_argument("--collection-id", required=True, help="Collection ID.")
    collection_update.add_argument("--title", help="Collection title.")
    collection_update.add_argument("--description", help="Collection description.")
    collection_update.add_argument("--agent-ids", help=_json_array_help("agent IDs"))
    add_bool_text_argument(collection_update, "--shared", help_text="Whether the collection is shared.")
    add_bool_text_argument(collection_update, "--is-public", help_text="Whether the collection is public.")
    add_json_data_argument(collection_update)
    collection_update.set_defaults(handler=task_agent_cmd._cmd_task_agent_collection_update, command="task-agent collection update")

    collection_add_agent = collection_sub.add_parser(
        "add-agent",
        help="Add an agent to a collection.",
        **rich_parser_kwargs("Add one agent to a collection.", examples=["vectorvein task-agent collection add-agent --collection-id collection_xxx --agent-id agent_xxx"]),
    )
    collection_add_agent.add_argument("--collection-id", required=True, help="Collection ID.")
    collection_add_agent.add_argument("--agent-id", required=True, help="Agent ID.")
    collection_add_agent.set_defaults(handler=task_agent_cmd._cmd_task_agent_collection_add_agent, command="task-agent collection add-agent")

    collection_remove_agent = collection_sub.add_parser(
        "remove-agent",
        help="Remove an agent from a collection.",
        **rich_parser_kwargs("Remove one agent from a collection.", examples=["vectorvein task-agent collection remove-agent --collection-id collection_xxx --agent-id agent_xxx"]),
    )
    collection_remove_agent.add_argument("--collection-id", required=True, help="Collection ID.")
    collection_remove_agent.add_argument("--agent-id", required=True, help="Agent ID.")
    collection_remove_agent.set_defaults(handler=task_agent_cmd._cmd_task_agent_collection_remove_agent, command="task-agent collection remove-agent")


def _register_mcp_server_group(task_agent_sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    mcp_server_parser = task_agent_sub.add_parser(
        "mcp-server",
        help="Register, inspect, and test MCP servers.",
        **rich_parser_kwargs("Manage MCP servers available to task agents.", examples=["vectorvein task-agent mcp-server test-connection --data @server.json"]),
    )
    mcp_server_sub = mcp_server_parser.add_subparsers(dest="task_agent_mcp_server_command")
    mcp_server_sub.required = True

    mcp_list = mcp_server_sub.add_parser(
        "list", help="List MCP servers.", **rich_parser_kwargs("List MCP servers.", examples=["vectorvein task-agent mcp-server list --search vector"])
    )
    add_paging_arguments(mcp_list)
    add_search_argument(mcp_list)
    add_json_data_argument(mcp_list)
    mcp_list.set_defaults(handler=task_agent_cmd._cmd_task_agent_mcp_server_list, command="task-agent mcp-server list")

    def _add_mcp_server_payload_args(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--name", help="Server display name.")
        parser.add_argument("--description", help="Server description.")
        parser.add_argument("--server-url", help="Server URL.")
        parser.add_argument("--transport-type", help="Transport type.")
        parser.add_argument("--headers", help=_json_object_help("HTTP headers"))
        parser.add_argument("--config", help=_json_object_help("server configuration"))
        add_json_data_argument(parser)

    mcp_create = mcp_server_sub.add_parser(
        "create",
        help="Create an MCP server.",
        **rich_parser_kwargs("Create an MCP server registration.", examples=["vectorvein task-agent mcp-server create --name docs --server-url https://example.com"]),
    )
    _add_mcp_server_payload_args(mcp_create)
    mcp_create.set_defaults(handler=task_agent_cmd._cmd_task_agent_mcp_server_create, command="task-agent mcp-server create")

    mcp_get = mcp_server_sub.add_parser(
        "get", help="Get an MCP server.", **rich_parser_kwargs("Fetch one MCP server by ID.", examples=["vectorvein task-agent mcp-server get --server-id server_xxx"])
    )
    mcp_get.add_argument("--server-id", required=True, help="Server ID.")
    mcp_get.set_defaults(handler=task_agent_cmd._cmd_task_agent_mcp_server_get, command="task-agent mcp-server get")

    mcp_update = mcp_server_sub.add_parser(
        "update",
        help="Update an MCP server.",
        **rich_parser_kwargs("Update an MCP server registration.", examples=["vectorvein task-agent mcp-server update --server-id server_xxx --name 'Updated name'"]),
    )
    mcp_update.add_argument("--server-id", required=True, help="Server ID.")
    _add_mcp_server_payload_args(mcp_update)
    mcp_update.set_defaults(handler=task_agent_cmd._cmd_task_agent_mcp_server_update, command="task-agent mcp-server update")

    mcp_delete = mcp_server_sub.add_parser(
        "delete",
        help="Delete an MCP server.",
        **rich_parser_kwargs("Delete an MCP server registration.", examples=["vectorvein task-agent mcp-server delete --server-id server_xxx"]),
    )
    mcp_delete.add_argument("--server-id", required=True, help="Server ID.")
    mcp_delete.set_defaults(handler=task_agent_cmd._cmd_task_agent_mcp_server_delete, command="task-agent mcp-server delete")

    mcp_test = mcp_server_sub.add_parser(
        "test-connection",
        help="Test a new MCP server connection.",
        **rich_parser_kwargs(
            "Test an MCP server connection before saving it.",
            examples=["vectorvein task-agent mcp-server test-connection --server-url https://example.com"],
            notes=["Provide either explicit connection flags or a --data JSON object."],
        ),
    )
    _add_mcp_server_payload_args(mcp_test)
    mcp_test.set_defaults(handler=task_agent_cmd._cmd_task_agent_mcp_server_test_connection, command="task-agent mcp-server test-connection")

    mcp_test_existing = mcp_server_sub.add_parser(
        "test-existing-server",
        help="Test a saved MCP server.",
        **rich_parser_kwargs("Test a saved MCP server registration by ID.", examples=["vectorvein task-agent mcp-server test-existing-server --server-id server_xxx"]),
    )
    mcp_test_existing.add_argument("--server-id", required=True, help="Server ID.")
    mcp_test_existing.set_defaults(handler=task_agent_cmd._cmd_task_agent_mcp_server_test_existing, command="task-agent mcp-server test-existing-server")


def _register_mcp_tool_group(task_agent_sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    mcp_tool_parser = task_agent_sub.add_parser(
        "mcp-tool",
        help="List, create, and inspect MCP tools.",
        **rich_parser_kwargs("Manage MCP tools available to agents.", examples=["vectorvein task-agent mcp-tool list --server-id server_xxx"]),
    )
    mcp_tool_sub = mcp_tool_parser.add_subparsers(dest="task_agent_mcp_tool_command")
    mcp_tool_sub.required = True

    mcp_tool_list = mcp_tool_sub.add_parser(
        "list", help="List MCP tools.", **rich_parser_kwargs("List MCP tools.", examples=["vectorvein task-agent mcp-tool list --server-id server_xxx"])
    )
    add_paging_arguments(mcp_tool_list)
    add_search_argument(mcp_tool_list)
    mcp_tool_list.add_argument("--server-id", help="Filter by MCP server ID.")
    add_json_data_argument(mcp_tool_list)
    mcp_tool_list.set_defaults(handler=task_agent_cmd._cmd_task_agent_mcp_tool_list, command="task-agent mcp-tool list")

    def _add_mcp_tool_payload_args(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--tool-name", help="Tool name.")
        parser.add_argument("--description", help="Tool description.")
        parser.add_argument("--server-id", help="MCP server ID.")
        parser.add_argument("--tool-schema", help=_json_object_help("tool schema"))
        add_json_data_argument(parser)

    mcp_tool_create = mcp_tool_sub.add_parser(
        "create",
        help="Create an MCP tool.",
        **rich_parser_kwargs("Create an MCP tool registration.", examples=["vectorvein task-agent mcp-tool create --tool-name docs-search --server-id server_xxx"]),
    )
    _add_mcp_tool_payload_args(mcp_tool_create)
    mcp_tool_create.set_defaults(handler=task_agent_cmd._cmd_task_agent_mcp_tool_create, command="task-agent mcp-tool create")

    mcp_tool_get = mcp_tool_sub.add_parser(
        "get", help="Get an MCP tool.", **rich_parser_kwargs("Fetch one MCP tool by ID.", examples=["vectorvein task-agent mcp-tool get --tool-id tool_xxx"])
    )
    mcp_tool_get.add_argument("--tool-id", required=True, help="Tool ID.")
    mcp_tool_get.set_defaults(handler=task_agent_cmd._cmd_task_agent_mcp_tool_get, command="task-agent mcp-tool get")

    mcp_tool_update = mcp_tool_sub.add_parser(
        "update",
        help="Update an MCP tool.",
        **rich_parser_kwargs("Update an MCP tool registration.", examples=["vectorvein task-agent mcp-tool update --tool-id tool_xxx --tool-name updated"]),
    )
    mcp_tool_update.add_argument("--tool-id", required=True, help="Tool ID.")
    _add_mcp_tool_payload_args(mcp_tool_update)
    mcp_tool_update.set_defaults(handler=task_agent_cmd._cmd_task_agent_mcp_tool_update, command="task-agent mcp-tool update")

    mcp_tool_delete = mcp_tool_sub.add_parser(
        "delete", help="Delete an MCP tool.", **rich_parser_kwargs("Delete an MCP tool registration.", examples=["vectorvein task-agent mcp-tool delete --tool-id tool_xxx"])
    )
    mcp_tool_delete.add_argument("--tool-id", required=True, help="Tool ID.")
    mcp_tool_delete.set_defaults(handler=task_agent_cmd._cmd_task_agent_mcp_tool_delete, command="task-agent mcp-tool delete")

    mcp_tool_logs = mcp_tool_sub.add_parser(
        "logs",
        help="Get MCP tool logs.",
        **rich_parser_kwargs("Fetch paginated logs for an MCP tool.", examples=["vectorvein task-agent mcp-tool logs --tool-id tool_xxx --page 1 --page-size 20"]),
    )
    mcp_tool_logs.add_argument("--tool-id", required=True, help="Tool ID.")
    add_paging_arguments(mcp_tool_logs, default_page_size=20)
    mcp_tool_logs.set_defaults(handler=task_agent_cmd._cmd_task_agent_mcp_tool_logs, command="task-agent mcp-tool logs")


def _register_user_memory_group(task_agent_sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    memory_parser = task_agent_sub.add_parser(
        "user-memory",
        help="Create, list, and maintain user memory records.",
        **rich_parser_kwargs("Manage persistent user memory entries used by agents.", examples=["vectorvein task-agent user-memory create --content 'Remember my preference.'"]),
    )
    memory_sub = memory_parser.add_subparsers(dest="task_agent_user_memory_command")
    memory_sub.required = True

    def _add_user_memory_payload_args(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--content", help="Memory content.")
        parser.add_argument("--memory-type", help="Memory type.")
        parser.add_argument("--metadata", help=_json_object_help("memory metadata"))
        add_bool_text_argument(parser, "--is-active", help_text="Whether the memory is active.")
        add_json_data_argument(parser)

    memory_create = memory_sub.add_parser(
        "create",
        help="Create a memory record.",
        **rich_parser_kwargs("Create a user memory record.", examples=["vectorvein task-agent user-memory create --content 'Remember I prefer markdown.'"]),
    )
    _add_user_memory_payload_args(memory_create)
    memory_create.set_defaults(handler=task_agent_cmd._cmd_task_agent_user_memory_create, command="task-agent user-memory create")

    memory_get = memory_sub.add_parser(
        "get", help="Get one memory record.", **rich_parser_kwargs("Fetch one user memory record by ID.", examples=["vectorvein task-agent user-memory get --memory-id memory_xxx"])
    )
    memory_get.add_argument("--memory-id", required=True, help="Memory ID.")
    memory_get.set_defaults(handler=task_agent_cmd._cmd_task_agent_user_memory_get, command="task-agent user-memory get")

    memory_list = memory_sub.add_parser(
        "list",
        help="List memory records.",
        **rich_parser_kwargs("List user memory records.", examples=["vectorvein task-agent user-memory list --memory-type preference --is-active true"]),
    )
    add_paging_arguments(memory_list, default_page_size=20)
    memory_list.add_argument("--memory-type", help="Memory type filter.")
    add_bool_text_argument(memory_list, "--is-active", help_text="Filter by active state.")
    add_search_argument(memory_list)
    memory_list.set_defaults(handler=task_agent_cmd._cmd_task_agent_user_memory_list, command="task-agent user-memory list")

    memory_update = memory_sub.add_parser(
        "update",
        help="Update a memory record.",
        **rich_parser_kwargs("Update a user memory record.", examples=["vectorvein task-agent user-memory update --memory-id memory_xxx --content 'Updated memory'"]),
    )
    memory_update.add_argument("--memory-id", required=True, help="Memory ID.")
    _add_user_memory_payload_args(memory_update)
    memory_update.set_defaults(handler=task_agent_cmd._cmd_task_agent_user_memory_update, command="task-agent user-memory update")

    memory_delete = memory_sub.add_parser(
        "delete", help="Delete a memory record.", **rich_parser_kwargs("Delete a user memory record.", examples=["vectorvein task-agent user-memory delete --memory-id memory_xxx"])
    )
    memory_delete.add_argument("--memory-id", required=True, help="Memory ID.")
    memory_delete.set_defaults(handler=task_agent_cmd._cmd_task_agent_user_memory_delete, command="task-agent user-memory delete")

    memory_toggle = memory_sub.add_parser(
        "toggle",
        help="Toggle a memory record active state.",
        **rich_parser_kwargs("Toggle a memory record active state.", examples=["vectorvein task-agent user-memory toggle --memory-id memory_xxx"]),
    )
    memory_toggle.add_argument("--memory-id", required=True, help="Memory ID.")
    memory_toggle.set_defaults(handler=task_agent_cmd._cmd_task_agent_user_memory_toggle, command="task-agent user-memory toggle")

    memory_stats = memory_sub.add_parser(
        "stats", help="Get memory statistics.", **rich_parser_kwargs("Fetch user memory statistics.", examples=["vectorvein task-agent user-memory stats"])
    )
    memory_stats.set_defaults(handler=task_agent_cmd._cmd_task_agent_user_memory_stats, command="task-agent user-memory stats")

    memory_batch_delete = memory_sub.add_parser(
        "batch-delete",
        help="Delete multiple memory records.",
        **rich_parser_kwargs("Delete multiple memory records at once.", examples=['vectorvein task-agent user-memory batch-delete --memory-ids \'["memory_1","memory_2"]\'']),
    )
    memory_batch_delete.add_argument("--memory-ids", required=True, help=_json_array_help("memory IDs"))
    memory_batch_delete.set_defaults(handler=task_agent_cmd._cmd_task_agent_user_memory_batch_delete, command="task-agent user-memory batch-delete")

    memory_batch_toggle = memory_sub.add_parser(
        "batch-toggle",
        help="Toggle multiple memory records.",
        **rich_parser_kwargs(
            "Set the active state for multiple memory records.", examples=["vectorvein task-agent user-memory batch-toggle --memory-ids '[\"memory_1\"]' --is-active true"]
        ),
    )
    memory_batch_toggle.add_argument("--memory-ids", required=True, help=_json_array_help("memory IDs"))
    add_bool_text_argument(memory_batch_toggle, "--is-active", help_text="Target active state.")
    memory_batch_toggle.set_defaults(handler=task_agent_cmd._cmd_task_agent_user_memory_batch_toggle, command="task-agent user-memory batch-toggle")

    memory_types = memory_sub.add_parser(
        "types", help="List supported memory types.", **rich_parser_kwargs("List supported user memory types.", examples=["vectorvein task-agent user-memory types"])
    )
    memory_types.set_defaults(handler=task_agent_cmd._cmd_task_agent_user_memory_types, command="task-agent user-memory types")


def _register_skill_group(task_agent_sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    skill_parser = task_agent_sub.add_parser(
        "skill",
        help="Browse, create, install, and maintain skills.",
        **rich_parser_kwargs("Manage reusable skills and skill installations.", examples=["vectorvein task-agent skill install --skill-id skill_xxx --permission-level auto"]),
    )
    skill_sub = skill_parser.add_subparsers(dest="task_agent_skill_command")
    skill_sub.required = True

    def _add_skill_payload_args(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--name", help="Skill name.")
        parser.add_argument("--display-name", help="Skill display name.")
        parser.add_argument("--description", help="Skill description.")
        parser.add_argument("--content", help="Skill content.")
        parser.add_argument("--category-id", help="Skill category ID.")
        parser.add_argument("--permission-level", help="Permission level.")
        parser.add_argument("--metadata", help=_json_object_help("skill metadata"))
        add_json_data_argument(parser)

    skill_list = skill_sub.add_parser("list", help="List available skills.", **rich_parser_kwargs("List skills.", examples=["vectorvein task-agent skill list --search markdown"]))
    add_paging_arguments(skill_list, default_page_size=20)
    add_search_argument(skill_list)
    skill_list.add_argument("--category-id", help="Skill category ID filter.")
    add_json_data_argument(skill_list)
    skill_list.set_defaults(handler=task_agent_cmd._cmd_task_agent_skill_list, command="task-agent skill list")

    skill_my = skill_sub.add_parser(
        "my-skills", help="List your skills.", **rich_parser_kwargs("List skills created by the current user.", examples=["vectorvein task-agent skill my-skills --page-size 50"])
    )
    add_paging_arguments(skill_my, default_page_size=20)
    skill_my.set_defaults(handler=task_agent_cmd._cmd_task_agent_skill_my_skills, command="task-agent skill my-skills")

    skill_get = skill_sub.add_parser(
        "get", help="Get one skill.", **rich_parser_kwargs("Fetch one skill by ID.", examples=["vectorvein task-agent skill get --skill-id skill_xxx"])
    )
    skill_get.add_argument("--skill-id", required=True, help="Skill ID.")
    skill_get.set_defaults(handler=task_agent_cmd._cmd_task_agent_skill_get, command="task-agent skill get")

    skill_create = skill_sub.add_parser(
        "create",
        help="Create a skill.",
        **rich_parser_kwargs(
            "Create a skill using explicit flags or a merged --data payload.",
            examples=["vectorvein task-agent skill create --name summarize --display-name 'Summarize Skill' --content @skill.json"],
        ),
    )
    _add_skill_payload_args(skill_create)
    skill_create.set_defaults(handler=task_agent_cmd._cmd_task_agent_skill_create, command="task-agent skill create")

    skill_upload = skill_sub.add_parser(
        "upload-and-parse",
        help="Upload a skill package and parse it.",
        **rich_parser_kwargs(
            "Upload a skill archive and let the backend parse it.", examples=["vectorvein task-agent skill upload-and-parse --path ./demo.skill --filename demo.skill"]
        ),
    )
    skill_upload.add_argument("--path", required=True, help="Local skill archive path.")
    skill_upload.add_argument("--filename", help="Filename to send to the API. Defaults to the local file name.")
    skill_upload.set_defaults(handler=task_agent_cmd._cmd_task_agent_skill_upload_and_parse, command="task-agent skill upload-and-parse")

    skill_update = skill_sub.add_parser(
        "update",
        help="Update a skill.",
        **rich_parser_kwargs("Update an existing skill.", examples=["vectorvein task-agent skill update --skill-id skill_xxx --display-name 'Updated name'"]),
    )
    skill_update.add_argument("--skill-id", required=True, help="Skill ID.")
    _add_skill_payload_args(skill_update)
    skill_update.set_defaults(handler=task_agent_cmd._cmd_task_agent_skill_update, command="task-agent skill update")

    skill_delete = skill_sub.add_parser(
        "delete", help="Delete a skill.", **rich_parser_kwargs("Delete a skill by ID.", examples=["vectorvein task-agent skill delete --skill-id skill_xxx"])
    )
    skill_delete.add_argument("--skill-id", required=True, help="Skill ID.")
    skill_delete.set_defaults(handler=task_agent_cmd._cmd_task_agent_skill_delete, command="task-agent skill delete")

    skill_install = skill_sub.add_parser(
        "install",
        help="Install a skill.",
        **rich_parser_kwargs("Install a skill globally or for a specific agent.", examples=["vectorvein task-agent skill install --skill-id skill_xxx --permission-level auto"]),
    )
    skill_install.add_argument("--skill-id", required=True, help="Skill ID.")
    skill_install.add_argument("--agent-id", help="Optional target agent ID.")
    skill_install.add_argument("--permission-level", help="Permission level.")
    skill_install.set_defaults(handler=task_agent_cmd._cmd_task_agent_skill_install, command="task-agent skill install")

    skill_uninstall = skill_sub.add_parser(
        "uninstall",
        help="Uninstall a skill.",
        **rich_parser_kwargs("Uninstall a skill globally or from a specific agent.", examples=["vectorvein task-agent skill uninstall --skill-id skill_xxx --agent-id agent_xxx"]),
    )
    skill_uninstall.add_argument("--skill-id", required=True, help="Skill ID.")
    skill_uninstall.add_argument("--agent-id", help="Optional agent ID.")
    skill_uninstall.set_defaults(handler=task_agent_cmd._cmd_task_agent_skill_uninstall, command="task-agent skill uninstall")

    skill_installed = skill_sub.add_parser(
        "installed",
        help="List installed skills.",
        **rich_parser_kwargs("List installed skills, optionally for a specific agent.", examples=["vectorvein task-agent skill installed --agent-id agent_xxx"]),
    )
    skill_installed.add_argument("--agent-id", help="Optional agent ID.")
    skill_installed.set_defaults(handler=task_agent_cmd._cmd_task_agent_skill_installed, command="task-agent skill installed")

    skill_update_installation = skill_sub.add_parser(
        "update-installation",
        help="Update a skill installation.",
        **rich_parser_kwargs(
            "Update installation-specific skill settings.", examples=["vectorvein task-agent skill update-installation --installation-id install_xxx --is-enabled true"]
        ),
    )
    skill_update_installation.add_argument("--installation-id", required=True, help="Installation ID.")
    add_bool_text_argument(skill_update_installation, "--is-enabled", help_text="Whether the installation is enabled.")
    skill_update_installation.add_argument("--permission-level", help="Permission level.")
    skill_update_installation.add_argument("--metadata", help=_json_object_help("installation metadata"))
    add_json_data_argument(skill_update_installation)
    skill_update_installation.set_defaults(handler=task_agent_cmd._cmd_task_agent_skill_update_installation, command="task-agent skill update-installation")

    skill_set_override = skill_sub.add_parser(
        "set-agent-override",
        help="Override a skill for one agent.",
        **rich_parser_kwargs(
            "Set per-agent enabled state for a skill.", examples=["vectorvein task-agent skill set-agent-override --skill-id skill_xxx --agent-id agent_xxx --is-enabled true"]
        ),
    )
    skill_set_override.add_argument("--skill-id", required=True, help="Skill ID.")
    skill_set_override.add_argument("--agent-id", required=True, help="Agent ID.")
    add_bool_text_argument(skill_set_override, "--is-enabled", help_text="Whether the skill is enabled for that agent.")
    skill_set_override.set_defaults(handler=task_agent_cmd._cmd_task_agent_skill_set_agent_override, command="task-agent skill set-agent-override")

    skill_remove_override = skill_sub.add_parser(
        "remove-agent-override",
        help="Remove a skill override for one agent.",
        **rich_parser_kwargs("Remove a per-agent skill override.", examples=["vectorvein task-agent skill remove-agent-override --skill-id skill_xxx --agent-id agent_xxx"]),
    )
    skill_remove_override.add_argument("--skill-id", required=True, help="Skill ID.")
    skill_remove_override.add_argument("--agent-id", required=True, help="Agent ID.")
    skill_remove_override.set_defaults(handler=task_agent_cmd._cmd_task_agent_skill_remove_agent_override, command="task-agent skill remove-agent-override")

    skill_categories = skill_sub.add_parser(
        "categories", help="List skill categories.", **rich_parser_kwargs("List available skill categories.", examples=["vectorvein task-agent skill categories"])
    )
    skill_categories.set_defaults(handler=task_agent_cmd._cmd_task_agent_skill_categories, command="task-agent skill categories")


def _register_skill_review_group(task_agent_sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    review_parser = task_agent_sub.add_parser(
        "skill-review",
        help="Create and inspect skill reviews.",
        **rich_parser_kwargs("Manage skill reviews.", examples=["vectorvein task-agent skill-review create --skill-id skill_xxx --rating 5 --comment 'Great skill'"]),
    )
    review_sub = review_parser.add_subparsers(dest="task_agent_skill_review_command")
    review_sub.required = True

    review_list = review_sub.add_parser(
        "list", help="List reviews for one skill.", **rich_parser_kwargs("List reviews for a skill.", examples=["vectorvein task-agent skill-review list --skill-id skill_xxx"])
    )
    review_list.add_argument("--skill-id", required=True, help="Skill ID.")
    add_paging_arguments(review_list, default_page_size=20)
    review_list.set_defaults(handler=task_agent_cmd._cmd_task_agent_skill_review_list, command="task-agent skill-review list")

    review_create = review_sub.add_parser(
        "create",
        help="Create a review.",
        **rich_parser_kwargs("Create a review for a skill.", examples=["vectorvein task-agent skill-review create --skill-id skill_xxx --rating 5 --comment 'Helpful.'"]),
    )
    review_create.add_argument("--skill-id", required=True, help="Skill ID.")
    review_create.add_argument("--rating", required=True, type=int, help="Rating value.")
    review_create.add_argument("--comment", help="Review comment.")
    review_create.set_defaults(handler=task_agent_cmd._cmd_task_agent_skill_review_create, command="task-agent skill-review create")

    review_delete = review_sub.add_parser(
        "delete",
        help="Delete a review.",
        **rich_parser_kwargs("Delete a skill review by review ID.", examples=["vectorvein task-agent skill-review delete --review-id review_xxx"]),
    )
    review_delete.add_argument("--review-id", required=True, help="Review ID.")
    review_delete.set_defaults(handler=task_agent_cmd._cmd_task_agent_skill_review_delete, command="task-agent skill-review delete")


def _register_task_category_group(task_agent_sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = task_agent_sub.add_parser(
        "task-category",
        help="List task categories.",
        **rich_parser_kwargs("List task categories used by the task-agent system.", examples=["vectorvein task-agent task-category list"]),
    )
    sub = parser.add_subparsers(dest="task_agent_task_category_command")
    sub.required = True
    cmd = sub.add_parser("list", help="List task categories.", **rich_parser_kwargs("List task categories.", examples=["vectorvein task-agent task-category list"]))
    cmd.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_category_list, command="task-agent task-category list")


def _register_tool_category_group(task_agent_sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = task_agent_sub.add_parser(
        "tool-category",
        help="List workflow tool categories.",
        **rich_parser_kwargs("List tool categories used for workflow tools.", examples=["vectorvein task-agent tool-category list"]),
    )
    sub = parser.add_subparsers(dest="task_agent_tool_category_command")
    sub.required = True
    cmd = sub.add_parser("list", help="List tool categories.", **rich_parser_kwargs("List workflow tool categories.", examples=["vectorvein task-agent tool-category list"]))
    cmd.set_defaults(handler=task_agent_cmd._cmd_task_agent_tool_category_list, command="task-agent tool-category list")


def _register_workflow_tool_group(task_agent_sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = task_agent_sub.add_parser(
        "workflow-tool",
        help="Publish workflows as reusable tools.",
        **rich_parser_kwargs(
            "Manage workflow tools that can be exposed to task agents.", examples=["vectorvein task-agent workflow-tool batch-create --workflow-wids '[\"wf_1\"]'"]
        ),
    )
    sub = parser.add_subparsers(dest="task_agent_workflow_tool_command")
    sub.required = True

    def _add_list_args(cmd: argparse.ArgumentParser) -> None:
        add_paging_arguments(cmd)
        add_search_argument(cmd)
        cmd.add_argument("--category-id", help="Category ID filter.")
        add_json_data_argument(cmd)

    official_list = sub.add_parser(
        "official-list",
        help="List official workflow tools.",
        **rich_parser_kwargs("List official workflow tools.", examples=["vectorvein task-agent workflow-tool official-list --category-id cat_xxx"]),
    )
    _add_list_args(official_list)
    official_list.set_defaults(handler=task_agent_cmd._cmd_task_agent_workflow_tool_official_list, command="task-agent workflow-tool official-list")

    my_list = sub.add_parser(
        "my-list",
        help="List your workflow tools.",
        **rich_parser_kwargs("List workflow tools created by the current user.", examples=["vectorvein task-agent workflow-tool my-list"]),
    )
    _add_list_args(my_list)
    my_list.set_defaults(handler=task_agent_cmd._cmd_task_agent_workflow_tool_my_list, command="task-agent workflow-tool my-list")

    def _add_workflow_tool_payload_args(cmd: argparse.ArgumentParser) -> None:
        cmd.add_argument("--workflow-wid", help="Workflow WID.")
        cmd.add_argument("--template-tid", help="Template TID.")
        cmd.add_argument("--category-id", help="Category ID.")
        cmd.add_argument("--display-name", help="Display name.")
        cmd.add_argument("--description", help="Description.")
        add_json_data_argument(cmd)

    workflow_tool_create = sub.add_parser(
        "create",
        help="Create one workflow tool.",
        **rich_parser_kwargs("Create a workflow tool.", examples=["vectorvein task-agent workflow-tool create --workflow-wid wf_xxx --category-id cat_xxx"]),
    )
    _add_workflow_tool_payload_args(workflow_tool_create)
    workflow_tool_create.set_defaults(handler=task_agent_cmd._cmd_task_agent_workflow_tool_create, command="task-agent workflow-tool create")

    workflow_tool_update = sub.add_parser(
        "update",
        help="Update one workflow tool.",
        **rich_parser_kwargs("Update a workflow tool.", examples=["vectorvein task-agent workflow-tool update --tool-id tool_xxx --display-name 'Updated'"]),
    )
    workflow_tool_update.add_argument("--tool-id", required=True, help="Tool ID.")
    _add_workflow_tool_payload_args(workflow_tool_update)
    workflow_tool_update.set_defaults(handler=task_agent_cmd._cmd_task_agent_workflow_tool_update, command="task-agent workflow-tool update")

    workflow_tool_delete = sub.add_parser(
        "delete", help="Delete one workflow tool.", **rich_parser_kwargs("Delete a workflow tool.", examples=["vectorvein task-agent workflow-tool delete --tool-id tool_xxx"])
    )
    workflow_tool_delete.add_argument("--tool-id", required=True, help="Tool ID.")
    workflow_tool_delete.set_defaults(handler=task_agent_cmd._cmd_task_agent_workflow_tool_delete, command="task-agent workflow-tool delete")

    workflow_tool_detail = sub.add_parser(
        "detail",
        help="Get workflow tool detail.",
        **rich_parser_kwargs("Fetch workflow tool detail by tool ID.", examples=["vectorvein task-agent workflow-tool detail --tool-id tool_xxx"]),
    )
    workflow_tool_detail.add_argument("--tool-id", required=True, help="Tool ID.")
    workflow_tool_detail.set_defaults(handler=task_agent_cmd._cmd_task_agent_workflow_tool_detail, command="task-agent workflow-tool detail")

    workflow_tool_batch_create = sub.add_parser(
        "batch-create",
        help="Create workflow tools in batch.",
        **rich_parser_kwargs(
            "Create workflow tools from multiple workflows or templates.",
            examples=["vectorvein task-agent workflow-tool batch-create --workflow-wids '[\"wf_1\"]' --template-tids '[\"tpl_1\"]' --category-id cat_xxx"],
        ),
    )
    workflow_tool_batch_create.add_argument("--workflow-wids", help=_json_array_help("workflow WIDs"))
    workflow_tool_batch_create.add_argument("--template-tids", help=_json_array_help("template TIDs"))
    workflow_tool_batch_create.add_argument("--category-id", help="Category ID.")
    workflow_tool_batch_create.set_defaults(handler=task_agent_cmd._cmd_task_agent_workflow_tool_batch_create, command="task-agent workflow-tool batch-create")


def _register_task_schedule_group(task_agent_sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = task_agent_sub.add_parser(
        "task-schedule",
        help="Manage recurring agent task schedules.",
        **rich_parser_kwargs(
            "Manage recurring task schedules for agents.", examples=["vectorvein task-agent task-schedule update --cron-expression '0 0 * * *' --agent-id agent_xxx"]
        ),
    )
    sub = parser.add_subparsers(dest="task_agent_task_schedule_command")
    sub.required = True

    schedule_list = sub.add_parser(
        "list", help="List task schedules.", **rich_parser_kwargs("List task schedules.", examples=["vectorvein task-agent task-schedule list --agent-id agent_xxx --enabled true"])
    )
    add_paging_arguments(schedule_list)
    add_search_argument(schedule_list)
    schedule_list.add_argument("--agent-id", help="Agent ID filter.")
    add_bool_text_argument(schedule_list, "--enabled", help_text="Filter by enabled state.")
    add_json_data_argument(schedule_list)
    schedule_list.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_schedule_list, command="task-agent task-schedule list")

    schedule_get = sub.add_parser(
        "get",
        help="Get one task schedule.",
        **rich_parser_kwargs("Fetch one task schedule by schedule ID.", examples=["vectorvein task-agent task-schedule get --schedule-id sid_xxx"]),
    )
    schedule_get.add_argument("--schedule-id", required=True, help="Schedule ID.")
    schedule_get.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_schedule_get, command="task-agent task-schedule get")

    schedule_update = sub.add_parser(
        "update",
        help="Create or update a task schedule.",
        **rich_parser_kwargs(
            "Create or update a task schedule.",
            examples=["vectorvein task-agent task-schedule update --cron-expression '0 0 * * *' --agent-id agent_xxx --task-info @task-info.json"],
            notes=["--task-info must be a JSON object. --mounted-cloud-storage-paths must be a JSON array or @file."],
        ),
    )
    schedule_update.add_argument("--cron-expression", required=True, help="Cron expression.")
    schedule_update.add_argument("--schedule-id", help="Existing schedule ID (sid). Omit to create.")
    schedule_update.add_argument("--agent-id", help="Agent ID.")
    schedule_update.add_argument("--timezone", help="Timezone string.")
    schedule_update.add_argument("--title", help="Schedule title.")
    schedule_update.add_argument("--task-info", help=_json_object_help("task_info"))
    schedule_update.add_argument("--mounted-cloud-storage-paths", help=_json_array_help("mounted cloud storage paths"))
    schedule_update.add_argument("--max-cycles", type=int, help="Max cycles.")
    add_bool_text_argument(schedule_update, "--send-email", help_text="Whether to send email notifications.")
    add_bool_text_argument(schedule_update, "--load-user-memory", help_text="Whether to load user memory.")
    schedule_update.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_schedule_update, command="task-agent task-schedule update")

    schedule_delete = sub.add_parser(
        "delete",
        help="Delete a task schedule.",
        **rich_parser_kwargs("Delete a task schedule by ID.", examples=["vectorvein task-agent task-schedule delete --schedule-id sid_xxx"]),
    )
    schedule_delete.add_argument("--schedule-id", required=True, help="Schedule ID.")
    schedule_delete.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_schedule_delete, command="task-agent task-schedule delete")

    schedule_toggle = sub.add_parser(
        "toggle",
        help="Enable or disable a task schedule.",
        **rich_parser_kwargs("Toggle a task schedule enabled state.", examples=["vectorvein task-agent task-schedule toggle --schedule-id sid_xxx --enabled true"]),
    )
    schedule_toggle.add_argument("--schedule-id", required=True, help="Schedule ID.")
    add_bool_text_argument(schedule_toggle, "--enabled", help_text="Target enabled state.")
    schedule_toggle.set_defaults(handler=task_agent_cmd._cmd_task_agent_task_schedule_toggle, command="task-agent task-schedule toggle")


def register_task_agent_parser(top_level: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    task_agent_parser = top_level.add_parser(
        "task-agent",
        help="Task-agent related commands.",
        **rich_parser_kwargs(
            "Manage reusable agents, tasks, cycles, skills, memory, and related task-agent resources.",
            examples=[
                "vectorvein task-agent agent create --name 'Research Assistant'",
                "vectorvein task-agent task create --agent-id agent_xxx --text 'Summarize this report' --wait",
                "vectorvein task-agent skill install --skill-id skill_xxx --permission-level auto",
            ],
        ),
    )
    task_agent_sub = task_agent_parser.add_subparsers(dest="task_agent_group")
    task_agent_sub.required = True

    _register_agent_group(task_agent_sub)
    _register_task_group(task_agent_sub)
    _register_cycle_group(task_agent_sub)
    _register_tag_group(task_agent_sub)
    _register_collection_group(task_agent_sub)
    _register_mcp_server_group(task_agent_sub)
    _register_mcp_tool_group(task_agent_sub)
    _register_user_memory_group(task_agent_sub)
    _register_skill_group(task_agent_sub)
    _register_skill_review_group(task_agent_sub)
    _register_task_category_group(task_agent_sub)
    _register_tool_category_group(task_agent_sub)
    _register_workflow_tool_group(task_agent_sub)
    _register_task_schedule_group(task_agent_sub)
