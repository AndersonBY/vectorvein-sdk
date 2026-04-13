import asyncio
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from vectorvein.api.task_agent import TaskAgentAsyncMixin, TaskAgentSyncMixin, _create_agent_from_response
from vectorvein.cli._output import CLIUsageError
from vectorvein.cli._parsers import _load_optional_agent_definition, _load_optional_agent_settings


_AGENT_RESPONSE = {
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
    "default_load_user_memory": True,
    "default_compress_memory_after_tokens": 64000,
    "default_agent_type": "computer",
    "default_workspace_files": [{"name": "README.md", "oss_path": "oss://bucket/readme"}],
    "default_sub_agent_ids": ["sub_agent_1"],
    "required_skills": [{"skill_id": "skill_1", "required": True}],
    "required_skills_count": 1,
    "default_output_verifier": "def main(): return '{}'",
    "default_computer_pod_setting_id": "pod_1",
    "default_cloud_storage_paths": ["/documents/reports"],
    "default_cloud_storage_write_enabled": True,
    "available_workflows": [{"wid": "wf_1", "title": "Workflow One"}],
    "available_workflow_templates": [{"tid": "tpl_1", "title": "Template One"}],
    "available_mcp_tools": [{"tool_id": "tool_1", "tool_name": "Search"}],
    "tags": [{"tid": "tag_1", "title": "Office"}],
    "shared": False,
    "is_public": False,
    "used_count": 0,
    "is_official": False,
    "official_order": 0,
    "is_owner": True,
    "is_favorited": True,
    "create_time": "2026-01-01T00:00:00Z",
    "update_time": "2026-01-01T00:00:00Z",
}


class _SyncRecorder(TaskAgentSyncMixin):
    def __init__(self):
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append((method, endpoint, kwargs))
        return {"status": 200, "msg": "", "data": _AGENT_RESPONSE}


class _AsyncRecorder(TaskAgentAsyncMixin):
    def __init__(self):
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append((method, endpoint, kwargs))
        return {"status": 200, "msg": "", "data": _AGENT_RESPONSE}


def test_create_agent_from_response_uses_token_threshold_schema():
    agent = _create_agent_from_response(_AGENT_RESPONSE)

    assert agent.default_compress_memory_after_tokens == 64000
    assert not hasattr(agent, "default_compress_memory_after_characters")
    assert agent.default_load_user_memory is True
    assert agent.required_skills_count == 1
    assert agent.default_computer_pod_setting_id == "pod_1"
    assert agent.default_cloud_storage_paths == ["/documents/reports"]
    assert agent.default_cloud_storage_write_enabled is True
    assert agent.available_mcp_tools == [{"tool_id": "tool_1", "tool_name": "Search"}]
    assert agent.tags == [{"tid": "tag_1", "title": "Office"}]
    assert agent.is_favorited is True


def test_sync_create_agent_sends_latest_agent_schema_fields():
    client = _SyncRecorder()

    client.create_agent(
        name="Agent One",
        usage_hint={"task_tip": "Summarize reports"},
        default_load_user_memory=True,
        default_compress_memory_after_tokens=64000,
        default_agent_type="computer",
        default_workspace_files=[{"name": "README.md", "oss_path": "oss://bucket/readme"}],
        default_sub_agent_ids=["sub_agent_1"],
        required_skills=[{"skill_id": "skill_1", "required": True}],
        default_output_verifier="def main(): return '{}'",
        default_computer_pod_setting_id="pod_1",
        default_cloud_storage_paths=["/documents/reports"],
        default_cloud_storage_write_enabled=True,
        available_mcp_tool_ids=["tool_1"],
        tag_ids=["tag_1"],
    )

    method, endpoint, kwargs = client.calls[0]
    payload = kwargs["json"]

    assert method == "POST"
    assert endpoint == "task-agent/agent/create"
    assert payload["default_compress_memory_after_tokens"] == 64000
    assert "default_compress_memory_after_characters" not in payload
    assert payload["default_load_user_memory"] is True
    assert payload["default_agent_type"] == "computer"
    assert payload["default_workspace_files"] == [{"name": "README.md", "oss_path": "oss://bucket/readme"}]
    assert payload["default_sub_agent_ids"] == ["sub_agent_1"]
    assert payload["required_skills"] == [{"skill_id": "skill_1", "required": True}]
    assert payload["default_output_verifier"] == "def main(): return '{}'"
    assert payload["default_computer_pod_setting_id"] == "pod_1"
    assert payload["default_cloud_storage_paths"] == ["/documents/reports"]
    assert payload["default_cloud_storage_write_enabled"] is True
    assert payload["available_mcp_tool_ids"] == ["tool_1"]
    assert payload["tag_ids"] == ["tag_1"]


def test_sync_update_agent_sends_latest_agent_schema_fields():
    client = _SyncRecorder()

    client.update_agent(
        agent_id="agent_1",
        usage_hint={"task_tip": "Summarize reports"},
        default_load_user_memory=False,
        default_compress_memory_after_tokens=96000,
        default_agent_type="tool",
        default_workspace_files=[{"name": "guide.md", "oss_path": "oss://bucket/guide"}],
        default_sub_agent_ids=["sub_agent_2"],
        required_skills=[{"skill_id": "skill_2", "required": True}],
        default_output_verifier="def main(): return '{\"ok\": true}'",
        default_computer_pod_setting_id="pod_2",
        default_cloud_storage_paths=["/knowledge-base"],
        default_cloud_storage_write_enabled=False,
        available_mcp_tool_ids=["tool_2"],
        tag_ids=["tag_2"],
    )

    _, endpoint, kwargs = client.calls[0]
    payload = kwargs["json"]

    assert endpoint == "task-agent/agent/update"
    assert payload["default_compress_memory_after_tokens"] == 96000
    assert "default_compress_memory_after_characters" not in payload
    assert payload["default_load_user_memory"] is False
    assert payload["default_agent_type"] == "tool"
    assert payload["default_workspace_files"] == [{"name": "guide.md", "oss_path": "oss://bucket/guide"}]
    assert payload["default_sub_agent_ids"] == ["sub_agent_2"]
    assert payload["required_skills"] == [{"skill_id": "skill_2", "required": True}]
    assert payload["default_output_verifier"] == "def main(): return '{\"ok\": true}'"
    assert payload["default_computer_pod_setting_id"] == "pod_2"
    assert payload["default_cloud_storage_paths"] == ["/knowledge-base"]
    assert payload["default_cloud_storage_write_enabled"] is False
    assert payload["available_mcp_tool_ids"] == ["tool_2"]
    assert payload["tag_ids"] == ["tag_2"]


def test_async_create_agent_sends_latest_agent_schema_fields():
    async def _run():
        client = _AsyncRecorder()
        await client.create_agent(
            name="Agent One",
            default_load_user_memory=True,
            default_compress_memory_after_tokens=64000,
            default_agent_type="computer",
            available_mcp_tool_ids=["tool_1"],
        )
        _, endpoint, kwargs = client.calls[0]
        payload = kwargs["json"]

        assert endpoint == "task-agent/agent/create"
        assert payload["default_compress_memory_after_tokens"] == 64000
        assert "default_compress_memory_after_characters" not in payload
        assert payload["default_load_user_memory"] is True
        assert payload["default_agent_type"] == "computer"
        assert payload["available_mcp_tool_ids"] == ["tool_1"]

    asyncio.run(_run())


def test_cli_agent_definition_parser_accepts_token_field_only():
    parsed = _load_optional_agent_definition(
        '{"model_name":"gpt-4o","backend_type":"openai","compress_memory_after_tokens":64000,"agent_type":"computer","workspace_files":[],"sub_agent_ids":[]}'
    )

    assert parsed is not None
    assert parsed.compress_memory_after_tokens == 64000


def test_cli_agent_definition_parser_rejects_legacy_character_field():
    with pytest.raises(CLIUsageError, match="AgentDefinition schema"):
        _load_optional_agent_definition('{"model_name":"gpt-4o","backend_type":"openai","compress_memory_after_characters":64000}')


def test_cli_agent_settings_parser_accepts_token_field_only():
    parsed = _load_optional_agent_settings(
        '{"model_name":"gpt-4o","backend_type":"openai","compress_memory_after_tokens":64000,"agent_type":"computer","computer_pod_setting_id":"pod_1"}'
    )

    assert parsed is not None
    assert parsed.compress_memory_after_tokens == 64000


def test_cli_agent_settings_parser_rejects_legacy_character_field():
    with pytest.raises(CLIUsageError, match="AgentSettings schema"):
        _load_optional_agent_settings('{"compress_memory_after_characters":64000}')
