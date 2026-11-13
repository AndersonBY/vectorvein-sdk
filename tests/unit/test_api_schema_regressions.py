"""Current backend responses exercised through both SDK clients."""

import asyncio
from dataclasses import asdict
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from vectorvein.api import APIKeyError, AsyncVectorVeinClient, VectorVeinAPIError, VectorVeinClient
from vectorvein.api.models import AgentDefinition, AgentSettings, TaskInfo
from vectorvein.cli._parser_builder import build_parser
from vectorvein.cli._output import CLIUsageError


@pytest.fixture(params=[False, True], ids=["sync", "async"])
def sdk(request):
    asynchronous = request.param
    cls = AsyncVectorVeinClient if asynchronous else VectorVeinClient
    client = cls(api_key="test-key")
    client._request = AsyncMock() if asynchronous else Mock()

    def invoke(method, data, *args, **kwargs):
        client._request.return_value = {"status": 200, "msg": "", "data": data}
        result = getattr(client, method)(*args, **kwargs)
        return asyncio.run(result) if asynchronous else result

    yield client, invoke
    if asynchronous:
        asyncio.run(client._client.aclose())
    else:
        client._client.close()


_FILE = {
    "key": "workspace/report.txt",
    "relative_path": "report.txt",
    "size": 3,
    "etag": "digest",
    "is_dir": False,
    "oss_path": "workspace/report.txt",
    "revision_id": "revision_1",
    "node_id": "node_1",
    "updated_revision": "revision_1",
    "content_sha256": "digest",
    "path": "report.txt",
}
_WORKSPACE = {
    "workspace_id": "workspace_1",
    "user": {"nickname": "User", "avatar": ""},
    "scope": "PROJECT",
    "revision": 3,
    "project_id": "project_1",
    "task_count": 2,
    "oss_bucket": "bucket",
    "base_storage_path": "workspace",
    "created_at": "date",
    "last_accessed": "date",
    "latest_files": [_FILE],
    "file_count": 1,
    "current_size_bytes": 3,
    "max_size_bytes": 1024,
    "can_write": False,
    "write_blocked_reason": "Use Project HEAD or Task Worktree",
}


def test_workspace_parses_current_summary_without_agent_task_id(sdk):
    _, invoke = sdk
    workspace = invoke("get_agent_workspace", _WORKSPACE, "workspace_1")
    assert workspace.agent_task_id is None
    assert workspace.project_id == "project_1"
    assert workspace.latest_files[0].relative_path == "report.txt"
    assert workspace.latest_files[0].last_modified is None
    assert workspace.can_write is False
    assert workspace.current_size_bytes == 3


def test_workspace_files_preserve_capabilities_and_forward_pagination(sdk):
    client, invoke = sdk
    result = invoke(
        "list_workspace_files",
        {
            "files": [_FILE],
            "tree_view": False,
            "can_write": False,
            "write_blocked_reason": "Read only",
            "has_more": True,
            "next_cursor": "next",
        },
        "workspace_1",
        page_size=1,
        cursor="previous",
        recursive=False,
        task_id="task_1",
    )
    assert result.files[0].revision_id == "revision_1"
    assert result.can_write is False
    assert result.next_cursor == "next"
    assert client._request.call_args.kwargs["json"] == {
        "workspace_id": "workspace_1",
        "tree_view": False,
        "page_size": 1,
        "cursor": "previous",
        "recursive": False,
        "task_id": "task_1",
    }
    content = invoke("read_workspace_file", {"content": "abc", "file_info": _FILE, "file_path": "report.txt"}, "workspace_1", "report.txt")
    assert content.file_info.content_sha256 == "digest"


def test_workflow_tag_matches_backend_title_schema(sdk):
    _, invoke = sdk
    workflow = invoke(
        "get_workflow",
        {
            "wid": "workflow_1",
            "title": "Workflow",
            "brief": "",
            "data": {},
            "language": "en",
            "images": [],
            "tags": [{"tid": "tag_1", "title": "Tag", "is_public": True, "language": "en", "color": "#123456"}],
        },
        "workflow_1",
    )
    assert workflow.tags[0].title == "Tag"
    assert workflow.tags[0].color == "#123456"


def test_task_preserves_multiple_questions_and_runtime_metadata(sdk):
    _, invoke = sdk
    waiting = {
        "cycle_id": "cycle_1",
        "tool_call_id": "call_1",
        "question": None,
        "questions": [{"id": "q1", "question": "Select", "options": ["A", "B"]}],
        "options": ["A", "B"],
        "selection_type": "multiple",
        "allow_custom_options": True,
        "metadata": {"source": "user"},
        "annotations": {"title": "Input"},
    }
    task = invoke(
        "get_agent_task",
        {
            "task_id": "task_1",
            "status": "WAIT_RESPONSE",
            "waiting_question": waiting,
            "project_id": "project_1",
            "worktree_id": "tree_1",
            "environment_expired": True,
            "permissions": {"can_write": False},
            "pending_messages": [{"message": "queued"}],
            "total_cached_tokens": 12,
            "total_used_credits": 3,
            "sub_task_runs": [{"status": "RUNNING"}],
        },
        "task_1",
    )
    assert asdict(task.waiting_question) == waiting
    assert task.project_id == "project_1"
    assert task.worktree_id == "tree_1"
    assert task.permissions == {"can_write": False}
    assert task.environment_expired is True
    assert task.pending_messages == [{"message": "queued"}]
    assert task.total_cached_tokens == 12


def test_dataclass_task_overrides_omit_unset_values(sdk):
    client, invoke = sdk
    invoke(
        "create_agent_task",
        {"task_id": "task_1"},
        TaskInfo(text="Hello", reasoning_effort="high"),
        agent_id_to_start="agent_1",
        agent_settings=AgentSettings(allow_interruption=False, sandbox_resource_tier="free"),
        max_cycles=0,
    )
    payload = client._request.call_args.kwargs["json"]
    assert payload["agent_settings"] == {"allow_interruption": False, "sandbox_resource_tier": "free"}
    assert payload["task_info"]["reasoning_effort"] == "high"
    assert payload["max_cycles"] == 0
    assert "custom_backend_type" not in payload["task_info"]
    definition = AgentDefinition("model", "backend", reasoning_effort="high", progress_mode="verbose", sandbox_resource_tier="free")
    assert definition.progress_mode == "verbose"


def test_access_key_list_constructs_objects_from_simple_serializer(sdk):
    _, invoke = sdk
    key = {
        "access_key": "key_1",
        "access_key_type": "M",
        "use_count": 0,
        "max_use_count": 5,
        "max_credits": 10,
        "used_credits": 0,
        "status": "AC",
        "access_scope": "S",
        "description": "",
        "create_time": "date",
        "expire_time": "date",
        "last_use_time": None,
    }
    result = invoke("list_access_keys", {"access_keys": [key], "total": 1, "page": 1, "page_size": 10})
    assert result.access_keys[0].access_key == "key_1"
    assert result.access_keys[0].v_app is None
    assert result.access_keys[0].records == []
    app = {"app_id": "app_1", "title": "App", "description": "", "info": {}, "images": [], "status": "NORMAL"}
    result = invoke("get_access_keys", [{**key, "v_app": app, "v_apps": [app]}], ["key_1"])
    assert result[0].v_app.app_id == "app_1"
    assert result[0].v_app.status == "NORMAL"
    assert result[0].v_apps[0].title == "App"


@pytest.mark.parametrize(
    "raw,status,expected",
    [
        ({"detail": "Credentials missing"}, 401, APIKeyError),
        ({"detail": "Forbidden"}, 403, VectorVeinAPIError),
        ({"status": 200, "msg": "upstream failure"}, 503, VectorVeinAPIError),
    ],
)
def test_http_errors_are_not_success_or_missing_status(raw, status, expected):
    with VectorVeinClient(api_key="test-key") as client:
        client._client.close()
        client._client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(status, json=raw)))
        with pytest.raises(expected) as error:
            client.get_user_info()
        assert error.value.status_code == status


@pytest.mark.parametrize("asynchronous", [False, True])
def test_transport_forwards_extra_headers_and_normalizes_slashes(asynchronous):
    requests = []

    def response(request):
        requests.append(request)
        return httpx.Response(200, json={"status": 200, "data": {}})

    async def run():
        async with AsyncVectorVeinClient(api_key="test-key", base_url="https://example.test/api/") as client:
            await client._client.aclose()
            client._client = httpx.AsyncClient(transport=httpx.MockTransport(response))
            await client._request("POST", "/workflow/get", headers={"X-Organization-ID": "org_1"})

    if asynchronous:
        asyncio.run(run())
    else:
        with VectorVeinClient(api_key="test-key", base_url="https://example.test/api/") as client:
            client._client.close()
            client._client = httpx.Client(transport=httpx.MockTransport(response))
            client._request("POST", "/workflow/get", headers={"X-Organization-ID": "org_1"})
    assert str(requests[0].url) == "https://example.test/api/workflow/get"
    assert requests[0].headers["X-Organization-ID"] == "org_1"
    assert requests[0].headers["VECTORVEIN-API-KEY"] == "test-key"


def test_removed_endpoints_are_not_advertised_in_sdk_or_cli():
    parser = build_parser()
    for method in ("create_mcp_tool", "update_mcp_tool", "delete_mcp_tool", "sync_workspace_container_to_oss"):
        assert not hasattr(VectorVeinClient, method)
        assert not hasattr(AsyncVectorVeinClient, method)
    for argv in (["task-agent", "mcp-tool", "create"], ["task-agent", "mcp-tool", "update"], ["task-agent", "mcp-tool", "delete"], ["agent-workspace", "sync"]):
        with pytest.raises(CLIUsageError, match="invalid choice"):
            parser.parse_args(argv)


def test_task_creation_forwards_project_and_explicit_false_flags(sdk):
    client, invoke = sdk
    invoke(
        "create_agent_task",
        {"task_id": "task_1"},
        TaskInfo(text="Hello"),
        agent_id_to_start="agent_1",
        project_id="project_1",
        load_user_memory=False,
        send_email=False,
        mounted_folder_ids=[],
        cloud_storage_write_enabled=False,
        is_hidden=False,
    )
    payload = client._request.call_args.kwargs["json"]
    assert payload["project_id"] == "project_1"
    assert payload["load_user_memory"] is False
    assert payload["send_email"] is False
    assert payload["mounted_folder_ids"] == []
    assert payload["cloud_storage_write_enabled"] is False
    invoke("list_agent_tasks", {"tasks": [], "total": 0, "page": 1, "page_size": 10, "page_count": 0}, project_id="project_1")
    assert client._request.call_args.kwargs["json"]["project_id"] == "project_1"


def test_cli_new_controls_reach_the_sdk():
    parser = build_parser()
    with VectorVeinClient(api_key="test-key") as client:
        client._request = Mock(return_value={"status": 200, "data": {"task_id": "task_1"}})
        args = parser.parse_args(["task-agent", "task", "create", "--agent-id", "agent_1", "--text", "Hello", "--project-id", "project_1", "--reasoning-effort", "high"])
        args.handler(args, client)
        payload = client._request.call_args.kwargs["json"]
        assert payload["project_id"] == "project_1"
        assert payload["task_info"]["reasoning_effort"] == "high"
        client._request.return_value = {"status": 200, "data": {"cycles": [], "total": 0, "returned_count": 0, "has_more": False}}
        args = parser.parse_args(["task-agent", "cycle", "list", "--task-id", "task_1", "--page-size", "2", "--offset", "10"])
        args.handler(args, client)
        assert client._request.call_args.kwargs["json"] == {"task_id": "task_1", "page_size": 2, "cycle_index_offset": 10}
