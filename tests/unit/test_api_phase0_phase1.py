import asyncio
import sys
from typing import Any
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from vectorvein.api import APIKeyError, RequestError, VectorVeinClient, VectorVeinAPIError
from vectorvein.api.agent_workspace import AgentWorkspaceAsyncMixin, AgentWorkspaceSyncMixin
from vectorvein.api.models import APIUserIdentity
from vectorvein.api.user import UserAsyncMixin, UserSyncMixin


_WORKSPACE_ITEM = {
    "workspace_id": "ws_1",
    "agent_task_id": "task_1",
    "user": {"nickname": "tester", "avatar": "https://example.com/a.png"},
    "oss_bucket": "bucket",
    "base_storage_path": "path",
    "created_at": "2026-01-01T00:00:00Z",
    "last_accessed": "2026-01-01T00:00:00Z",
    "latest_files": [],
    "file_count": 0,
}

_STUB_RESPONSE_BY_ENDPOINT = {
    "user-info/get": {"status": 200, "data": {"username": "tester", "credits": 100}},
    "user/validate-api-key": {"status": 200, "data": {"user_id": "1", "username": "tester"}},
    "agent-workspace/list": {
        "status": 200,
        "data": {"workspaces": [_WORKSPACE_ITEM], "total": 1, "page": 1, "page_size": 10, "page_count": 1},
    },
    "agent-workspace/get": {"status": 200, "data": _WORKSPACE_ITEM},
    "agent-workspace/list-files": {
        "status": 200,
        "data": {"files": [{"key": "a.txt", "size": 1, "etag": "e", "last_modified": "2026-01-01T00:00:00Z"}], "tree_view": False},
    },
    "agent-workspace/read-file": {
        "status": 200,
        "data": {
            "content": "hello",
            "file_info": {"key": "a.txt", "size": 1, "etag": "e", "last_modified": "2026-01-01T00:00:00Z"},
            "file_path": "a.txt",
        },
    },
    "agent-workspace/download-file": {"status": 200, "data": {"file_url": "https://example.com/file"}},
    "agent-workspace/write-file": {"status": 200, "data": {"result": "ok"}},
    "agent-workspace/delete-file": {"status": 200, "data": {"result": "ok"}},
    "agent-workspace/zip-files": {
        "status": 200,
        "data": {"oss_path": "oss://z.zip", "download_url": "https://example.com/z.zip", "file_count": 3, "workspace_id": "ws_1"},
    },
    "agent-workspace/sync-container-to-oss": {
        "status": 200,
        "data": {"message": "同步任务已触发", "workspace_id": "ws_1", "task_id": "task_1"},
    },
}


class _RecordingSyncClient(UserSyncMixin, AgentWorkspaceSyncMixin):
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def _request(self, method: str, endpoint: str, **_: Any) -> dict[str, Any]:
        self.calls.append((method, endpoint))
        return _STUB_RESPONSE_BY_ENDPOINT[endpoint]


class _RecordingAsyncClient(UserAsyncMixin, AgentWorkspaceAsyncMixin):
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    async def _request(self, method: str, endpoint: str, **_: Any) -> dict[str, Any]:
        self.calls.append((method, endpoint))
        return _STUB_RESPONSE_BY_ENDPOINT[endpoint]


def test_sync_endpoint_mapping_for_phase1_methods():
    client = _RecordingSyncClient()

    identity = client.validate_api_key()
    assert isinstance(identity, APIUserIdentity)
    assert client.get_user_info()["username"] == "tester"
    client.list_agent_workspaces(page=1, page_size=10)
    client.get_agent_workspace("ws_1")
    client.list_workspace_files("ws_1")
    client.read_workspace_file("ws_1", "a.txt")
    client.download_workspace_file("ws_1", "a.txt")
    client.write_workspace_file("ws_1", "a.txt", "hello")
    client.delete_workspace_file("ws_1", "a.txt")
    client.zip_workspace_files("ws_1")
    client.sync_workspace_container_to_oss("ws_1")

    assert client.calls == [
        ("GET", "user/validate-api-key"),
        ("GET", "user-info/get"),
        ("POST", "agent-workspace/list"),
        ("POST", "agent-workspace/get"),
        ("POST", "agent-workspace/list-files"),
        ("POST", "agent-workspace/read-file"),
        ("POST", "agent-workspace/download-file"),
        ("POST", "agent-workspace/write-file"),
        ("POST", "agent-workspace/delete-file"),
        ("POST", "agent-workspace/zip-files"),
        ("POST", "agent-workspace/sync-container-to-oss"),
    ]


def test_async_endpoint_mapping_for_phase1_methods():
    async def _run():
        client = _RecordingAsyncClient()

        identity = await client.validate_api_key()
        assert isinstance(identity, APIUserIdentity)
        assert (await client.get_user_info())["username"] == "tester"
        await client.list_agent_workspaces(page=1, page_size=10)
        await client.get_agent_workspace("ws_1")
        await client.list_workspace_files("ws_1")
        await client.read_workspace_file("ws_1", "a.txt")
        await client.download_workspace_file("ws_1", "a.txt")
        await client.write_workspace_file("ws_1", "a.txt", "hello")
        await client.delete_workspace_file("ws_1", "a.txt")
        await client.zip_workspace_files("ws_1")
        await client.sync_workspace_container_to_oss("ws_1")

        assert client.calls == [
            ("GET", "user/validate-api-key"),
            ("GET", "user-info/get"),
            ("POST", "agent-workspace/list"),
            ("POST", "agent-workspace/get"),
            ("POST", "agent-workspace/list-files"),
            ("POST", "agent-workspace/read-file"),
            ("POST", "agent-workspace/download-file"),
            ("POST", "agent-workspace/write-file"),
            ("POST", "agent-workspace/delete-file"),
            ("POST", "agent-workspace/zip-files"),
            ("POST", "agent-workspace/sync-container-to-oss"),
        ]

    asyncio.run(_run())


def test_base_request_error_mapping():
    with VectorVeinClient(api_key="x" * 32) as client:
        request = httpx.Request("GET", "https://example.com")

        # 401 -> APIKeyError with status code
        client._client.request = lambda **_: httpx.Response(200, request=request, json={"status": 401, "msg": "unauthorized"})  # type: ignore[method-assign]
        with pytest.raises(APIKeyError) as unauthorized:
            client._request("GET", "dummy")
        assert unauthorized.value.status_code == 401

        # 403 (generic business error) -> VectorVeinAPIError
        client._client.request = lambda **_: httpx.Response(200, request=request, json={"status": 403, "msg": "forbidden action"})  # type: ignore[method-assign]
        with pytest.raises(VectorVeinAPIError) as forbidden:
            client._request("GET", "dummy")
        assert forbidden.value.status_code == 403
        assert not isinstance(forbidden.value, APIKeyError)

        # 403 with api key semantics -> APIKeyError
        client._client.request = lambda **_: httpx.Response(200, request=request, json={"status": 403, "msg": "API key expired"})  # type: ignore[method-assign]
        with pytest.raises(APIKeyError) as expired_key:
            client._request("GET", "dummy")
        assert expired_key.value.status_code == 403

        # invalid JSON -> RequestError
        client._client.request = lambda **_: httpx.Response(200, request=request, content=b"not-json", headers={"content-type": "text/plain"})  # type: ignore[method-assign]
        with pytest.raises(RequestError):
            client._request("GET", "dummy")

        # missing status -> RequestError
        client._client.request = lambda **_: httpx.Response(200, request=request, json={"msg": "missing"})  # type: ignore[method-assign]
        with pytest.raises(RequestError):
            client._request("GET", "dummy")
