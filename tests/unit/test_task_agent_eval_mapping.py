import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from vectorvein.api.task_agent import TaskAgentAsyncMixin, TaskAgentSyncMixin


class _TaskAgentSyncRecorder(TaskAgentSyncMixin):
    def __init__(self):
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append((method, endpoint, kwargs.get("json") or {}))
        return {"status": 200, "msg": "", "data": {"ok": True}}


class _TaskAgentAsyncRecorder(TaskAgentAsyncMixin):
    def __init__(self):
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append((method, endpoint, kwargs.get("json") or {}))
        return {"status": 200, "msg": "", "data": {"ok": True}}


_EXPECTED_CALLS = [
    ("POST", "task-agent/agent-eval-dataset/create"),
    ("POST", "task-agent/agent-eval-dataset/get"),
    ("POST", "task-agent/agent-eval-dataset/list"),
    ("POST", "task-agent/agent-eval-dataset/update"),
    ("POST", "task-agent/agent-eval-dataset/delete"),
    ("POST", "task-agent/agent-eval-case/create"),
    ("POST", "task-agent/agent-eval-case/list"),
    ("POST", "task-agent/agent-eval-case/update"),
    ("POST", "task-agent/agent-eval-case/delete"),
    ("POST", "task-agent/agent-eval-run/create"),
    ("POST", "task-agent/agent-eval-run/get"),
    ("POST", "task-agent/agent-eval-run/list"),
    ("POST", "task-agent/agent-eval-run/cancel"),
    ("POST", "task-agent/agent-eval-run/results"),
    ("POST", "task-agent/agent-eval-run/case-results"),
]


def _exercise_sync(client: _TaskAgentSyncRecorder) -> None:
    client.create_agent_eval_dataset(name="Dataset", tags=["smoke"])
    client.get_agent_eval_dataset("dataset_1")
    client.list_agent_eval_datasets(page=1, page_size=20, search="Dataset")
    client.update_agent_eval_dataset("dataset_1", description="Updated")
    client.delete_agent_eval_dataset("dataset_1")
    client.create_agent_eval_case(dataset_id="dataset_1", title="Case", input_payload={"input": "x"})
    client.list_agent_eval_cases(dataset_id="dataset_1", page=1, page_size=50)
    client.update_agent_eval_case("case_1", metadata={"k": "v"})
    client.delete_agent_eval_case("case_1")
    client.create_agent_eval_run(dataset_id="dataset_1", candidate_config={"agent_id": "agent_1"})
    client.get_agent_eval_run("run_1")
    client.list_agent_eval_runs(dataset_id="dataset_1", page=1, page_size=20)
    client.cancel_agent_eval_run("run_1")
    client.get_agent_eval_run_results("run_1")
    client.list_agent_eval_case_results("run_1", candidate_id="candidate_1", case_run_id="case_run_1")


async def _exercise_async(client: _TaskAgentAsyncRecorder) -> None:
    await client.create_agent_eval_dataset(name="Dataset", tags=["smoke"])
    await client.get_agent_eval_dataset("dataset_1")
    await client.list_agent_eval_datasets(page=1, page_size=20, search="Dataset")
    await client.update_agent_eval_dataset("dataset_1", description="Updated")
    await client.delete_agent_eval_dataset("dataset_1")
    await client.create_agent_eval_case(dataset_id="dataset_1", title="Case", input_payload={"input": "x"})
    await client.list_agent_eval_cases(dataset_id="dataset_1", page=1, page_size=50)
    await client.update_agent_eval_case("case_1", metadata={"k": "v"})
    await client.delete_agent_eval_case("case_1")
    await client.create_agent_eval_run(dataset_id="dataset_1", candidate_config={"agent_id": "agent_1"})
    await client.get_agent_eval_run("run_1")
    await client.list_agent_eval_runs(dataset_id="dataset_1", page=1, page_size=20)
    await client.cancel_agent_eval_run("run_1")
    await client.get_agent_eval_run_results("run_1")
    await client.list_agent_eval_case_results("run_1", candidate_id="candidate_1", case_run_id="case_run_1")


def test_task_agent_eval_sync_endpoint_mapping_and_payloads():
    client = _TaskAgentSyncRecorder()
    _exercise_sync(client)

    assert [(method, endpoint) for method, endpoint, _ in client.calls] == _EXPECTED_CALLS
    assert client.calls[0][2] == {"name": "Dataset", "tags": ["smoke"]}
    assert client.calls[1][2] == {"dataset_id": "dataset_1"}
    assert client.calls[3][2] == {"dataset_id": "dataset_1", "description": "Updated"}
    assert client.calls[9][2] == {"dataset_id": "dataset_1", "candidate_config": {"agent_id": "agent_1"}}
    assert client.calls[14][2] == {"run_id": "run_1", "candidate_id": "candidate_1", "case_run_id": "case_run_1"}


def test_task_agent_eval_async_endpoint_mapping():
    async def _run():
        client = _TaskAgentAsyncRecorder()
        await _exercise_async(client)
        assert [(method, endpoint) for method, endpoint, _ in client.calls] == _EXPECTED_CALLS

    asyncio.run(_run())
