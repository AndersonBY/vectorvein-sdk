"""Cycle SDK/CLI parsing against the backend's paginated response shape."""

import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from vectorvein.api import VectorVeinClient
from vectorvein.api.task_agent import TaskAgentAsyncMixin, TaskAgentSyncMixin
from vectorvein.cli.main import main as cli_main


_CYCLE = {
    "cycle_id": "cycle_1",
    "details_revision": "revision_1",
    "agent_task_id": "task_1",
    "cycle_index": 2,
    "status": "COMPLETED",
    "ai_response": {"content": "Done"},
    "tool_calls": [],
    "tool_responses": [],
    "user_continuation_data": {"text": "Continue"},
    "has_user_continuation": True,
    "prompt_tokens": 10,
    "completion_tokens": 5,
    "cached_tokens": 3,
    "used_credits": 1,
    "start_time": "2026-11-14T00:00:00Z",
    "complete_time": "2026-11-14T00:00:01Z",
    "memory_compressed": False,
}
_PAGE = {
    "cycles": [_CYCLE],
    "returned_count": 1,
    "has_more": True,
    "next_start_index": 3,
    "next_end_index": None,
    "direction": "forward",
    "page_size": 50,
    "total": 52,
}


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("operation,data", [("list", _PAGE), ("get", _CYCLE)])
def test_cycle_api_parses_backend_response(asynchronous, operation, data):
    client = TaskAgentAsyncMixin() if asynchronous else TaskAgentSyncMixin()
    request = AsyncMock if asynchronous else Mock
    client._request = request(return_value={"status": 200, "data": data})
    result = client.list_agent_cycles("task_1", cycle_index_offset=2) if operation == "list" else client.get_agent_cycle("cycle_1")
    if asynchronous:
        result = asyncio.run(result)

    normalized = asdict(result)
    for key, value in data.items():
        if key == "cycles":
            for cycle_key, cycle_value in value[0].items():
                assert normalized[key][0][cycle_key] == cycle_value
            assert result.cycles[0].cycle_id == "cycle_1"
        else:
            assert normalized[key] == value
    if operation == "list":
        assert result.total > result.returned_count
        payload = {"task_id": "task_1", "cycle_index_offset": 2}
    else:
        payload = {"cycle_id": "cycle_1"}
    client._request.assert_called_once_with("POST", f"task-agent/agent-cycle/{operation}", json=payload)


@pytest.mark.parametrize("operation,data", [("list", _PAGE), ("get", _CYCLE)])
def test_cycle_cli_parses_backend_response(monkeypatch, capsys, operation, data):
    request = Mock(return_value={"status": 200, "data": data})
    monkeypatch.setattr(VectorVeinClient, "_request", request)
    identifier = ["--task-id", "task_1"] if operation == "list" else ["--cycle-id", "cycle_1"]

    exit_code = cli_main(["--api-key", "test-key", "--format", "json", "task-agent", "cycle", operation, *identifier])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["ok"] is True
    for key, value in data.items():
        if key == "cycles":
            for cycle_key, cycle_value in value[0].items():
                assert output["data"][key][0][cycle_key] == cycle_value
        else:
            assert output["data"][key] == value
