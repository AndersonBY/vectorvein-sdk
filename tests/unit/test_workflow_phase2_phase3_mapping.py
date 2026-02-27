import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from vectorvein.api.workflow import WorkflowAsyncMixin, WorkflowSyncMixin


def _workflow_response_for(endpoint: str) -> dict[str, Any]:
    if endpoint == "workflow/get":
        return {
            "status": 200,
            "msg": "",
            "data": {
                "wid": "wf_1",
                "title": "Workflow 1",
                "brief": "",
                "data": {"nodes": [], "edges": []},
                "language": "zh-CN",
                "images": [],
                "tags": [],
            },
        }
    if endpoint == "workflow/run-template":
        return {"status": 200, "msg": "", "data": {"rid": "rid_1"}}
    return {"status": 200, "msg": "", "data": {"ok": True}}


class _WorkflowSyncRecorder(WorkflowSyncMixin):
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def _request(self, method: str, endpoint: str, **_: Any) -> dict[str, Any]:
        self.calls.append((method, endpoint))
        return _workflow_response_for(endpoint)


class _WorkflowAsyncRecorder(WorkflowAsyncMixin):
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    async def _request(self, method: str, endpoint: str, **_: Any) -> dict[str, Any]:
        self.calls.append((method, endpoint))
        return _workflow_response_for(endpoint)


_EXPECTED_ENDPOINTS = [
    "workflow/get",
    "workflow/list",
    "workflow/update",
    "workflow/update-tool-call-data",
    "workflow/delete",
    "workflow/run-template",
    "workflow/resume-run",
    "workflow/stop-run",
    "workflow/run-record/get",
    "workflow/run-record/list",
    "workflow/run-record/stop",
    "workflow/run-record/delete",
    "workflow/run-schedule/list",
    "workflow/run-schedule/get",
    "workflow/run-schedule/update",
    "workflow/run-schedule/delete",
    "workflow/template/get",
    "workflow/template/update",
    "workflow/template/update-tool-call-data",
    "workflow/template/create",
    "workflow/template/list",
    "workflow/template/delete",
    "workflow/template/add",
    "workflow/template/api-download",
    "workflow/tag/create",
    "workflow/tag/delete",
    "workflow/tag/list",
    "workflow/tag/update",
    "workflow/tag/search",
    "workflow/trash/list",
    "workflow/trash/restore",
    "workflow/trash/purge",
    "workflow/fast-access/add",
    "workflow/fast-access/delete",
    "workflow/schedule-trigger/get",
    "workflow/schedule-trigger/update",
    "workflow/schedule-trigger/delete",
]


def _exercise_sync(client: _WorkflowSyncRecorder):
    client.get_workflow("wf_1")
    client.list_workflows()
    client.update_workflow("wf_1", data={"nodes": [], "edges": []})
    client.update_workflow_tool_call_data("wf_1", {"k": "v"})
    client.delete_workflow("wf_1")
    client.run_workflow_template("tpl_1", data={"nodes": [], "edges": []})
    client.resume_workflow_run("rid_1")
    client.stop_workflow_run("rid_1")
    client.get_workflow_run_record("rid_1")
    client.list_workflow_run_records()
    client.stop_workflow_run_record("rid_1")
    client.delete_workflow_run_record("rid_1")
    client.list_workflow_run_schedules()
    client.get_workflow_run_schedule("sid_1")
    client.update_workflow_run_schedule(cron_expression="0 0 * * *", wid="wf_1")
    client.delete_workflow_run_schedule("sid_1")
    client.get_workflow_template("tpl_1")
    client.update_workflow_template("tpl_1", data={"nodes": [], "edges": []})
    client.update_workflow_template_tool_call_data("tpl_1", {"k": "v"})
    client.create_workflow_template("wf_1")
    client.list_workflow_templates()
    client.delete_workflow_template("tpl_1")
    client.add_workflow_template("tpl_1")
    client.api_download_workflow_template("tpl_1")
    client.create_workflow_tag(title="tag")
    client.delete_workflow_tag("tag_1")
    client.list_workflow_tags()
    client.update_workflow_tag("tag_1", title="tag-2")
    client.search_workflow_tags("tag")
    client.list_workflow_trash()
    client.restore_workflow_from_trash("wf_1")
    client.purge_workflow_from_trash("wf_1")
    client.add_workflow_fast_access("wf_1")
    client.remove_workflow_fast_access("wf_1")
    client.get_workflow_schedule_trigger("wf_1")
    client.update_workflow_schedule_trigger("wf_1", data={"nodes": [], "edges": []})
    client.delete_workflow_schedule_trigger("wf_1")


async def _exercise_async(client: _WorkflowAsyncRecorder):
    await client.get_workflow("wf_1")
    await client.list_workflows()
    await client.update_workflow("wf_1", data={"nodes": [], "edges": []})
    await client.update_workflow_tool_call_data("wf_1", {"k": "v"})
    await client.delete_workflow("wf_1")
    await client.run_workflow_template("tpl_1", data={"nodes": [], "edges": []})
    await client.resume_workflow_run("rid_1")
    await client.stop_workflow_run("rid_1")
    await client.get_workflow_run_record("rid_1")
    await client.list_workflow_run_records()
    await client.stop_workflow_run_record("rid_1")
    await client.delete_workflow_run_record("rid_1")
    await client.list_workflow_run_schedules()
    await client.get_workflow_run_schedule("sid_1")
    await client.update_workflow_run_schedule(cron_expression="0 0 * * *", wid="wf_1")
    await client.delete_workflow_run_schedule("sid_1")
    await client.get_workflow_template("tpl_1")
    await client.update_workflow_template("tpl_1", data={"nodes": [], "edges": []})
    await client.update_workflow_template_tool_call_data("tpl_1", {"k": "v"})
    await client.create_workflow_template("wf_1")
    await client.list_workflow_templates()
    await client.delete_workflow_template("tpl_1")
    await client.add_workflow_template("tpl_1")
    await client.api_download_workflow_template("tpl_1")
    await client.create_workflow_tag(title="tag")
    await client.delete_workflow_tag("tag_1")
    await client.list_workflow_tags()
    await client.update_workflow_tag("tag_1", title="tag-2")
    await client.search_workflow_tags("tag")
    await client.list_workflow_trash()
    await client.restore_workflow_from_trash("wf_1")
    await client.purge_workflow_from_trash("wf_1")
    await client.add_workflow_fast_access("wf_1")
    await client.remove_workflow_fast_access("wf_1")
    await client.get_workflow_schedule_trigger("wf_1")
    await client.update_workflow_schedule_trigger("wf_1", data={"nodes": [], "edges": []})
    await client.delete_workflow_schedule_trigger("wf_1")


def test_workflow_phase2_phase3_sync_endpoint_mapping():
    client = _WorkflowSyncRecorder()
    _exercise_sync(client)

    assert client.calls == [("POST", endpoint) for endpoint in _EXPECTED_ENDPOINTS]


def test_workflow_phase2_phase3_async_endpoint_mapping():
    async def _run():
        client = _WorkflowAsyncRecorder()
        await _exercise_async(client)
        assert client.calls == [("POST", endpoint) for endpoint in _EXPECTED_ENDPOINTS]

    asyncio.run(_run())
