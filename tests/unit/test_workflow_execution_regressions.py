"""Workflow server-wait and polling responses must have identical semantics."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from vectorvein.api.exceptions import WorkflowError
from vectorvein.api.workflow import WorkflowAsyncMixin, WorkflowSyncMixin


_OUTPUT = [{"type": "text", "title": "Result", "value": "done"}]


def _invoke(asynchronous, method, responses, **kwargs):
    client = WorkflowAsyncMixin() if asynchronous else WorkflowSyncMixin()
    client._request = (AsyncMock if asynchronous else Mock)(side_effect=responses)
    result = getattr(client, method)(**kwargs)
    if asynchronous:
        result = asyncio.run(result)
    return client, result


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("data", [{}, {"progress": "running"}])
def test_pending_workflow_status_is_not_parsed_as_outputs(asynchronous, data):
    _, result = _invoke(asynchronous, "check_workflow_status", [{"status": 202, "msg": "RUNNING", "data": data}], rid="run_1")
    assert result.status == 202
    assert result.data == []


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("data", [_OUTPUT, {"wid": "workflow_1", "data": {"nodes": []}}])
def test_server_completed_workflow_returns_original_outputs_without_poll(asynchronous, data):
    client, result = _invoke(
        asynchronous, "run_workflow", [{"status": 200, "msg": "FINISHED", "rid": "run_1", "data": data}], wid="workflow_1", input_fields=[], wait_for_completion=True
    )
    assert client._request.call_count == 1
    assert result.rid == "run_1"
    if isinstance(data, list):
        assert result.data[0].value == "done"
    else:
        assert result.data == data


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_workflow_poll_survives_pending_status_and_reaches_completion(asynchronous, monkeypatch):
    monkeypatch.setattr("vectorvein.api.workflow.time.sleep", lambda _: None)
    monkeypatch.setattr("vectorvein.api.workflow.asyncio.sleep", AsyncMock())
    client, result = _invoke(
        asynchronous,
        "run_workflow",
        [
            {"status": 202, "msg": "accepted", "rid": "run_1", "data": {}},
            {"status": 202, "msg": "RUNNING", "data": {}},
            {"status": 200, "msg": "FINISHED", "data": _OUTPUT},
        ],
        wid="workflow_1",
        input_fields=[],
        wait_for_completion=True,
    )
    assert result.data[0].value == "done"
    assert client._request.call_count == 3
    assert client._request.call_args.kwargs["json"]["rid"] == "run_1"


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_missing_workflow_run_id_fails_before_polling(asynchronous):
    with pytest.raises(WorkflowError, match="run ID"):
        _invoke(asynchronous, "run_workflow", [{"status": 200, "msg": "timeout", "data": {}}], wid="workflow_1", input_fields=[], wait_for_completion=True)
