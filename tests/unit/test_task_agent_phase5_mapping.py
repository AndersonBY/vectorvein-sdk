import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from vectorvein.api.task_agent import TaskAgentAsyncMixin, TaskAgentSyncMixin


_AGENT_DATA = {
    "agent_id": "agent_1",
    "user": {"nickname": "tester", "avatar": "https://example.com/avatar.png"},
    "name": "Agent One",
    "avatar": "https://example.com/agent.png",
    "description": "desc",
    "system_prompt": "You are helpful.",
    "default_model_name": "gpt-4o",
    "default_backend_type": "openai",
    "default_max_cycles": 20,
    "default_allow_interruption": True,
    "default_use_workspace": True,
    "default_compress_memory_after_characters": 128000,
    "shared": False,
    "is_public": False,
    "used_count": 0,
    "is_official": False,
    "official_order": 0,
    "is_owner": True,
    "create_time": "2026-01-01T00:00:00Z",
    "update_time": "2026-01-01T00:00:00Z",
}


def _task_agent_response_for(endpoint: str) -> dict[str, Any]:
    if endpoint == "task-agent/agent/favorite-list":
        return {
            "status": 200,
            "msg": "",
            "data": {"agents": [_AGENT_DATA], "total": 1, "page": 1, "page_size": 10, "page_count": 1},
        }
    if endpoint == "task-agent/agent/create-optimized-agent":
        return {"status": 200, "msg": "", "data": _AGENT_DATA}
    return {"status": 200, "msg": "", "data": {"ok": True}}


class _TaskAgentSyncRecorder(TaskAgentSyncMixin):
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def _request(self, method: str, endpoint: str, **_: Any) -> dict[str, Any]:
        self.calls.append((method, endpoint))
        return _task_agent_response_for(endpoint)


class _TaskAgentAsyncRecorder(TaskAgentAsyncMixin):
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    async def _request(self, method: str, endpoint: str, **_: Any) -> dict[str, Any]:
        self.calls.append((method, endpoint))
        return _task_agent_response_for(endpoint)


_EXPECTED_ENDPOINTS = [
    "task-agent/agent/favorite-list",
    "task-agent/agent/toggle-favorite",
    "task-agent/agent/update-system-prompt",
    "task-agent/agent/create-optimized-agent",
    "task-agent/agent-task/computer-pod-settings",
    "task-agent/agent-task/batch-delete",
    "task-agent/agent-task/add-pending-message",
    "task-agent/agent-task/toggle-hidden",
    "task-agent/agent-task/toggle-favorite",
    "task-agent/agent-task/start-prompt-optimization",
    "task-agent/agent-task/get-prompt-optimizer-config",
    "task-agent/agent-task/close-computer-environment",
    "task-agent/agent-cycle/run-workflow",
    "task-agent/agent-cycle/check-workflow-status",
    "task-agent/agent-cycle/task-finish",
    "task-agent/agent-cycle/replay-cycles",
    "task-agent/agent-cycle/replay-summary",
]


def _exercise_sync(client: _TaskAgentSyncRecorder):
    client.list_favorite_agents(page=1, page_size=10)
    client.toggle_agent_favorite("agent_1", is_favorited=True)
    client.update_agent_system_prompt("agent_1", system_prompt="new prompt")
    client.create_optimized_agent("agent_1", system_prompt="better prompt", name="Optimized")
    client.list_computer_pod_settings()
    client.batch_delete_agent_tasks(["task_1", "task_2"])
    client.add_pending_message("task_1", "pending", action_type="queue")
    client.toggle_agent_task_hidden("task_1", is_hidden=True)
    client.toggle_agent_task_favorite("task_1", is_favorited=True)
    client.start_prompt_optimization("task_1", "optimize for stability")
    client.get_prompt_optimizer_config()
    client.close_computer_environment("task_1")
    client.run_agent_cycle_workflow("cycle_1", "tool_name", {"foo": "bar"})
    client.check_agent_cycle_workflow_status("rid_1")
    client.finish_agent_cycle_task("cycle_1", message="done")
    client.replay_agent_cycles("task_1", start_index=0, end_index=3)
    client.get_agent_replay_summary("task_1")


async def _exercise_async(client: _TaskAgentAsyncRecorder):
    await client.list_favorite_agents(page=1, page_size=10)
    await client.toggle_agent_favorite("agent_1", is_favorited=True)
    await client.update_agent_system_prompt("agent_1", system_prompt="new prompt")
    await client.create_optimized_agent("agent_1", system_prompt="better prompt", name="Optimized")
    await client.list_computer_pod_settings()
    await client.batch_delete_agent_tasks(["task_1", "task_2"])
    await client.add_pending_message("task_1", "pending", action_type="queue")
    await client.toggle_agent_task_hidden("task_1", is_hidden=True)
    await client.toggle_agent_task_favorite("task_1", is_favorited=True)
    await client.start_prompt_optimization("task_1", "optimize for stability")
    await client.get_prompt_optimizer_config()
    await client.close_computer_environment("task_1")
    await client.run_agent_cycle_workflow("cycle_1", "tool_name", {"foo": "bar"})
    await client.check_agent_cycle_workflow_status("rid_1")
    await client.finish_agent_cycle_task("cycle_1", message="done")
    await client.replay_agent_cycles("task_1", start_index=0, end_index=3)
    await client.get_agent_replay_summary("task_1")


def test_task_agent_phase5_sync_endpoint_mapping():
    client = _TaskAgentSyncRecorder()
    _exercise_sync(client)
    assert client.calls == [("POST", endpoint) for endpoint in _EXPECTED_ENDPOINTS]


def test_task_agent_phase5_async_endpoint_mapping():
    async def _run():
        client = _TaskAgentAsyncRecorder()
        await _exercise_async(client)
        assert client.calls == [("POST", endpoint) for endpoint in _EXPECTED_ENDPOINTS]

    asyncio.run(_run())
