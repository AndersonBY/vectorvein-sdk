import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from vectorvein.api.workflow import WorkflowAsyncMixin, WorkflowSyncMixin


class _WorkflowSyncRecorder(WorkflowSyncMixin):
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def _request(self, method: str, endpoint: str, **_: Any) -> dict[str, Any]:
        self.calls.append((method, endpoint))
        return {"status": 200, "msg": "", "data": {"ok": True}}


class _WorkflowAsyncRecorder(WorkflowAsyncMixin):
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    async def _request(self, method: str, endpoint: str, **_: Any) -> dict[str, Any]:
        self.calls.append((method, endpoint))
        return {"status": 200, "msg": "", "data": {"ok": True}}


_EXPECTED_ENDPOINTS = [
    "workflow/vector-database/check-access",
    "workflow/vector-database/get",
    "workflow/vector-database/update",
    "workflow/vector-database/create",
    "workflow/vector-database/list",
    "workflow/vector-database/delete",
    "workflow/vector-database-object/get",
    "workflow/vector-database-object/batch-get",
    "workflow/vector-database-object/update",
    "workflow/vector-database-object/create",
    "workflow/vector-database-object/list",
    "workflow/vector-database-object/delete",
    "workflow/vector-database-object-segment/get",
    "workflow/vector-database-object-segment/update",
    "workflow/vector-database-object-segment/list",
    "workflow/vector-database-object-segment/delete",
    "workflow/relational-database/get",
    "workflow/relational-database/update",
    "workflow/relational-database/create",
    "workflow/relational-database/list",
    "workflow/relational-database/delete",
    "workflow/relational-database/refresh",
    "workflow/relational-database/run-sql",
    "workflow/relational-database-table/get",
    "workflow/relational-database-table/update",
    "workflow/relational-database-table/refresh",
    "workflow/relational-database-table/create",
    "workflow/relational-database-table/list",
    "workflow/relational-database-table/delete",
    "workflow/relational-database-task/get-table-schema",
    "workflow/relational-database-task/refresh-table-max-rows",
    "workflow/relational-database-table-record/list",
    "workflow/relational-database-table-record/update",
    "workflow/relational-database-table-record/delete",
    "workflow/relational-database-table-record/add",
]


def _exercise_sync(client: _WorkflowSyncRecorder):
    client.check_vector_database_access("vid_1")
    client.get_vector_database("vid_1")
    client.update_vector_database("vid_1", name="db")
    client.create_vector_database(name="db")
    client.list_vector_databases(page=1, page_size=10)
    client.delete_vector_database("vid_1")
    client.get_vector_database_object("oid_1")
    client.batch_get_vector_database_objects("vid_1", ["oid_1", "oid_2"])
    client.update_vector_database_object("oid_1", title="doc")
    client.create_vector_database_object("vid_1", add_method="text", content="hello")
    client.list_vector_database_objects("vid_1", page=1, page_size=10)
    client.delete_vector_database_object("oid_1")
    client.get_vector_database_object_segment("oid_1")
    client.update_vector_database_object_segment("sid_1", enabled=True)
    client.list_vector_database_object_segments("oid_1", page=1, page_size=10)
    client.delete_vector_database_object_segment("oid_1")
    client.get_relational_database("rid_1")
    client.update_relational_database("rid_1", name="rdb")
    client.create_relational_database(name="rdb")
    client.list_relational_databases(page=1, page_size=10)
    client.delete_relational_database("rid_1")
    client.refresh_relational_database("rid_1")
    client.run_sql_on_relational_database("rid_1", "select 1")
    client.get_relational_database_table("tid_1")
    client.update_relational_database_table("tid_1", info={"k": "v"})
    client.refresh_relational_database_table("tid_1")
    client.create_relational_database_table(
        rid="rid_1",
        add_method="manual",
        files=[],
        sql_statement="",
        table_schema=[{"table_name": "t1", "columns": []}],
    )
    client.list_relational_database_tables("rid_1", page=1, page_size=10)
    client.delete_relational_database_table("tid_1")
    client.get_relational_database_table_schema(files=["oss://a.csv"])
    client.refresh_relational_database_table_max_rows(rid="rid_1")
    client.list_relational_database_table_records("tid_1", page=1, page_size=10)
    client.update_relational_database_table_records("tid_1", records=[{"id": 1}])
    client.delete_relational_database_table_records("tid_1", records=[{"id": 1}])
    client.add_relational_database_table_record("tid_1", add_method="manual", record={"id": 2})


async def _exercise_async(client: _WorkflowAsyncRecorder):
    await client.check_vector_database_access("vid_1")
    await client.get_vector_database("vid_1")
    await client.update_vector_database("vid_1", name="db")
    await client.create_vector_database(name="db")
    await client.list_vector_databases(page=1, page_size=10)
    await client.delete_vector_database("vid_1")
    await client.get_vector_database_object("oid_1")
    await client.batch_get_vector_database_objects("vid_1", ["oid_1", "oid_2"])
    await client.update_vector_database_object("oid_1", title="doc")
    await client.create_vector_database_object("vid_1", add_method="text", content="hello")
    await client.list_vector_database_objects("vid_1", page=1, page_size=10)
    await client.delete_vector_database_object("oid_1")
    await client.get_vector_database_object_segment("oid_1")
    await client.update_vector_database_object_segment("sid_1", enabled=True)
    await client.list_vector_database_object_segments("oid_1", page=1, page_size=10)
    await client.delete_vector_database_object_segment("oid_1")
    await client.get_relational_database("rid_1")
    await client.update_relational_database("rid_1", name="rdb")
    await client.create_relational_database(name="rdb")
    await client.list_relational_databases(page=1, page_size=10)
    await client.delete_relational_database("rid_1")
    await client.refresh_relational_database("rid_1")
    await client.run_sql_on_relational_database("rid_1", "select 1")
    await client.get_relational_database_table("tid_1")
    await client.update_relational_database_table("tid_1", info={"k": "v"})
    await client.refresh_relational_database_table("tid_1")
    await client.create_relational_database_table(
        rid="rid_1",
        add_method="manual",
        files=[],
        sql_statement="",
        table_schema=[{"table_name": "t1", "columns": []}],
    )
    await client.list_relational_database_tables("rid_1", page=1, page_size=10)
    await client.delete_relational_database_table("tid_1")
    await client.get_relational_database_table_schema(files=["oss://a.csv"])
    await client.refresh_relational_database_table_max_rows(rid="rid_1")
    await client.list_relational_database_table_records("tid_1", page=1, page_size=10)
    await client.update_relational_database_table_records("tid_1", records=[{"id": 1}])
    await client.delete_relational_database_table_records("tid_1", records=[{"id": 1}])
    await client.add_relational_database_table_record("tid_1", add_method="manual", record={"id": 2})


def test_workflow_phase4_sync_endpoint_mapping():
    client = _WorkflowSyncRecorder()
    _exercise_sync(client)
    assert client.calls == [("POST", endpoint) for endpoint in _EXPECTED_ENDPOINTS]


def test_workflow_phase4_async_endpoint_mapping():
    async def _run():
        client = _WorkflowAsyncRecorder()
        await _exercise_async(client)
        assert client.calls == [("POST", endpoint) for endpoint in _EXPECTED_ENDPOINTS]

    asyncio.run(_run())
