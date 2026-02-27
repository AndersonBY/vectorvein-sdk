import asyncio
import io
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from vectorvein.api.task_agent import TaskAgentAsyncMixin, TaskAgentSyncMixin


class _TaskAgentSyncRecorder(TaskAgentSyncMixin):
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def _request(self, method: str, endpoint: str, **_: Any) -> dict[str, Any]:
        self.calls.append((method, endpoint))
        return {"status": 200, "msg": "", "data": {"ok": True}}


class _TaskAgentAsyncRecorder(TaskAgentAsyncMixin):
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    async def _request(self, method: str, endpoint: str, **_: Any) -> dict[str, Any]:
        self.calls.append((method, endpoint))
        return {"status": 200, "msg": "", "data": {"ok": True}}


_EXPECTED_CALLS = [
    "task-agent/tag/create",
    "task-agent/tag/delete",
    "task-agent/tag/list",
    "task-agent/tag/update",
    "task-agent/tag/search",
    "task-agent/collection/create",
    "task-agent/collection/get",
    "task-agent/collection/list",
    "task-agent/collection/public-list",
    "task-agent/collection/update",
    "task-agent/collection/delete",
    "task-agent/collection/add-agent",
    "task-agent/collection/remove-agent",
    "task-agent/mcp-server/list",
    "task-agent/mcp-server/create",
    "task-agent/mcp-server/get",
    "task-agent/mcp-server/update",
    "task-agent/mcp-server/delete",
    "task-agent/mcp-server/test-connection",
    "task-agent/mcp-server/test-existing-server",
    "task-agent/mcp-tool/list",
    "task-agent/mcp-tool/create",
    "task-agent/mcp-tool/get",
    "task-agent/mcp-tool/update",
    "task-agent/mcp-tool/delete",
    "task-agent/mcp-tool/get-logs",
    "task-agent/user-memory/create",
    "task-agent/user-memory/get",
    "task-agent/user-memory/list",
    "task-agent/user-memory/update",
    "task-agent/user-memory/delete",
    "task-agent/user-memory/toggle",
    "task-agent/user-memory/stats",
    "task-agent/user-memory/batch-delete",
    "task-agent/user-memory/batch-toggle",
    "task-agent/user-memory/types",
    "task-agent/skill/list",
    "task-agent/skill/my-skills",
    "task-agent/skill/get",
    "task-agent/skill/create",
    "task-agent/skill/upload-and-parse",
    "task-agent/skill/update",
    "task-agent/skill/delete",
    "task-agent/skill/install",
    "task-agent/skill/uninstall",
    "task-agent/skill/installed",
    "task-agent/skill/update-installation",
    "task-agent/skill/set-agent-override",
    "task-agent/skill/remove-agent-override",
    "task-agent/skill/categories",
    "task-agent/skill-review/list",
    "task-agent/skill-review/create",
    "task-agent/skill-review/delete",
    "task-agent/task-category/list",
    "task-agent/tool-category/list",
    "task-agent/workflow-tool/official-list",
    "task-agent/workflow-tool/my-list",
    "task-agent/workflow-tool/create",
    "task-agent/workflow-tool/update",
    "task-agent/workflow-tool/delete",
    "task-agent/workflow-tool/detail",
    "task-agent/workflow-tool/batch-create",
    "task-agent/task-schedule/list",
    "task-agent/task-schedule/get",
    "task-agent/task-schedule/update",
    "task-agent/task-schedule/delete",
    "task-agent/task-schedule/toggle",
]

_GET_ENDPOINTS = {
    "task-agent/user-memory/stats",
    "task-agent/user-memory/types",
}


def _exercise_sync(client: _TaskAgentSyncRecorder):
    client.create_agent_tag("tag", color="#ffffff")
    client.delete_agent_tag("tag_1")
    client.list_agent_tags(public_only=True)
    client.update_agent_tags([{"tid": "tag_1", "title": "new"}])
    client.search_agent_tags("tag")
    client.create_agent_collection(title="Collection 1")
    client.get_agent_collection("collection_1")
    client.list_agent_collections(page=1, page_size=10)
    client.list_public_agent_collections(page=1, page_size=10)
    client.update_agent_collection("collection_1", title="Updated")
    client.delete_agent_collection("collection_1")
    client.add_agent_to_collection("collection_1", "agent_1")
    client.remove_agent_from_collection("collection_1", "agent_1")
    client.list_mcp_servers(page=1, page_size=10)
    client.create_mcp_server(name="mcp-server")
    client.get_mcp_server("server_1")
    client.update_mcp_server("server_1", name="updated")
    client.delete_mcp_server("server_1")
    client.test_mcp_server_connection(server_url="https://example.com")
    client.test_existing_mcp_server("server_1")
    client.list_mcp_tools(page=1, page_size=10)
    client.create_mcp_tool(tool_name="tool")
    client.get_mcp_tool("tool_1")
    client.update_mcp_tool("tool_1", tool_name="updated")
    client.delete_mcp_tool("tool_1")
    client.get_mcp_tool_logs("tool_1", page=1, page_size=20)
    client.create_user_memory(content="remember this")
    client.get_user_memory("memory_1")
    client.list_user_memories(page=1, page_size=20)
    client.update_user_memory("memory_1", content="updated")
    client.delete_user_memory("memory_1")
    client.toggle_user_memory("memory_1")
    client.get_user_memory_stats()
    client.batch_delete_user_memories(["memory_1", "memory_2"])
    client.batch_toggle_user_memories(["memory_1"], is_active=True)
    client.list_user_memory_types()
    client.list_skills(page=1, page_size=20)
    client.list_my_skills(page=1, page_size=20)
    client.get_skill("skill_1")
    client.create_skill(name="skill")
    client.upload_and_parse_skill(io.BytesIO(b"skill"), filename="demo.skill")
    client.update_skill("skill_1", display_name="Updated")
    client.delete_skill("skill_1")
    client.install_skill("skill_1", permission_level="auto")
    client.uninstall_skill("skill_1")
    client.list_installed_skills()
    client.update_skill_installation("install_1", is_enabled=True)
    client.set_skill_agent_override("skill_1", "agent_1", is_enabled=True)
    client.remove_skill_agent_override("skill_1", "agent_1")
    client.list_skill_categories()
    client.list_skill_reviews("skill_1", page=1, page_size=20)
    client.create_skill_review("skill_1", rating=5, comment="good")
    client.delete_skill_review("review_1")
    client.list_task_categories()
    client.list_tool_categories()
    client.list_official_workflow_tools(category_id="cat_1")
    client.list_my_workflow_tools(category_id="cat_1")
    client.create_workflow_tool(workflow_wid="wf_1")
    client.update_workflow_tool("tool_1", category_id="cat_1")
    client.delete_workflow_tool("tool_1")
    client.get_workflow_tool_detail("tool_1")
    client.batch_create_workflow_tools(workflow_wids=["wf_1"], template_tids=["tpl_1"])
    client.list_task_schedules(page=1, page_size=10)
    client.get_task_schedule("sid_1")
    client.update_task_schedule(cron_expression="0 0 * * *", agent_id="agent_1")
    client.delete_task_schedule("sid_1")
    client.toggle_task_schedule("sid_1", enabled=True)


async def _exercise_async(client: _TaskAgentAsyncRecorder):
    await client.create_agent_tag("tag", color="#ffffff")
    await client.delete_agent_tag("tag_1")
    await client.list_agent_tags(public_only=True)
    await client.update_agent_tags([{"tid": "tag_1", "title": "new"}])
    await client.search_agent_tags("tag")
    await client.create_agent_collection(title="Collection 1")
    await client.get_agent_collection("collection_1")
    await client.list_agent_collections(page=1, page_size=10)
    await client.list_public_agent_collections(page=1, page_size=10)
    await client.update_agent_collection("collection_1", title="Updated")
    await client.delete_agent_collection("collection_1")
    await client.add_agent_to_collection("collection_1", "agent_1")
    await client.remove_agent_from_collection("collection_1", "agent_1")
    await client.list_mcp_servers(page=1, page_size=10)
    await client.create_mcp_server(name="mcp-server")
    await client.get_mcp_server("server_1")
    await client.update_mcp_server("server_1", name="updated")
    await client.delete_mcp_server("server_1")
    await client.test_mcp_server_connection(server_url="https://example.com")
    await client.test_existing_mcp_server("server_1")
    await client.list_mcp_tools(page=1, page_size=10)
    await client.create_mcp_tool(tool_name="tool")
    await client.get_mcp_tool("tool_1")
    await client.update_mcp_tool("tool_1", tool_name="updated")
    await client.delete_mcp_tool("tool_1")
    await client.get_mcp_tool_logs("tool_1", page=1, page_size=20)
    await client.create_user_memory(content="remember this")
    await client.get_user_memory("memory_1")
    await client.list_user_memories(page=1, page_size=20)
    await client.update_user_memory("memory_1", content="updated")
    await client.delete_user_memory("memory_1")
    await client.toggle_user_memory("memory_1")
    await client.get_user_memory_stats()
    await client.batch_delete_user_memories(["memory_1", "memory_2"])
    await client.batch_toggle_user_memories(["memory_1"], is_active=True)
    await client.list_user_memory_types()
    await client.list_skills(page=1, page_size=20)
    await client.list_my_skills(page=1, page_size=20)
    await client.get_skill("skill_1")
    await client.create_skill(name="skill")
    await client.upload_and_parse_skill(io.BytesIO(b"skill"), filename="demo.skill")
    await client.update_skill("skill_1", display_name="Updated")
    await client.delete_skill("skill_1")
    await client.install_skill("skill_1", permission_level="auto")
    await client.uninstall_skill("skill_1")
    await client.list_installed_skills()
    await client.update_skill_installation("install_1", is_enabled=True)
    await client.set_skill_agent_override("skill_1", "agent_1", is_enabled=True)
    await client.remove_skill_agent_override("skill_1", "agent_1")
    await client.list_skill_categories()
    await client.list_skill_reviews("skill_1", page=1, page_size=20)
    await client.create_skill_review("skill_1", rating=5, comment="good")
    await client.delete_skill_review("review_1")
    await client.list_task_categories()
    await client.list_tool_categories()
    await client.list_official_workflow_tools(category_id="cat_1")
    await client.list_my_workflow_tools(category_id="cat_1")
    await client.create_workflow_tool(workflow_wid="wf_1")
    await client.update_workflow_tool("tool_1", category_id="cat_1")
    await client.delete_workflow_tool("tool_1")
    await client.get_workflow_tool_detail("tool_1")
    await client.batch_create_workflow_tools(workflow_wids=["wf_1"], template_tids=["tpl_1"])
    await client.list_task_schedules(page=1, page_size=10)
    await client.get_task_schedule("sid_1")
    await client.update_task_schedule(cron_expression="0 0 * * *", agent_id="agent_1")
    await client.delete_task_schedule("sid_1")
    await client.toggle_task_schedule("sid_1", enabled=True)


def test_task_agent_phase6_phase7_sync_endpoint_mapping():
    client = _TaskAgentSyncRecorder()
    _exercise_sync(client)
    assert client.calls == [("GET" if endpoint in _GET_ENDPOINTS else "POST", endpoint) for endpoint in _EXPECTED_CALLS]


def test_task_agent_phase6_phase7_async_endpoint_mapping():
    async def _run():
        client = _TaskAgentAsyncRecorder()
        await _exercise_async(client)
        assert client.calls == [("GET" if endpoint in _GET_ENDPOINTS else "POST", endpoint) for endpoint in _EXPECTED_CALLS]

    asyncio.run(_run())
