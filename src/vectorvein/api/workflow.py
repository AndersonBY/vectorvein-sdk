"""Workflow API functionality"""

import time
import asyncio
from typing import Any, Literal, overload

from .exceptions import WorkflowError, TimeoutError, VectorVeinAPIError
from .models import (
    WorkflowInputField,
    WorkflowOutput,
    WorkflowRunResult,
    Workflow,
    WorkflowTag,
)


class WorkflowMixin:
    """Workflow API mixin with shared logic"""

    @staticmethod
    def _create_workflow_response(response: dict[str, Any]) -> Workflow:
        """Parse workflow creation response"""
        workflow_tags = []
        if response["data"].get("tags"):
            for tag_data in response["data"]["tags"]:
                if isinstance(tag_data, dict):
                    workflow_tags.append(WorkflowTag(**tag_data))

        return Workflow(
            wid=response["data"]["wid"],
            title=response["data"]["title"],
            brief=response["data"]["brief"],
            data=response["data"]["data"],
            language=response["data"]["language"],
            images=response["data"]["images"],
            tags=workflow_tags,
            source_workflow=response["data"].get("source_workflow"),
            tool_call_data=response["data"].get("tool_call_data"),
            create_time=response["data"].get("create_time"),
            update_time=response["data"].get("update_time"),
        )

    @staticmethod
    def _parse_workflow_result(response: dict[str, Any], rid: str) -> WorkflowRunResult:
        """Parse workflow run result"""
        if response["status"] in [200, 202]:
            return WorkflowRunResult(
                rid=rid,
                status=response["status"],
                msg=response["msg"],
                data=[WorkflowOutput(**output) for output in response["data"]],
            )
        else:
            raise WorkflowError(f"Workflow execution failed: {response['msg']}")

    @staticmethod
    def _build_payload(base: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {} if base is None else dict(base)
        for key, value in kwargs.items():
            if value is not None:
                payload[key] = value
        return payload

    @staticmethod
    def _extract_data(response: dict[str, Any]) -> Any:
        return response.get("data", {})


class WorkflowSyncMixin(WorkflowMixin):
    """Synchronous workflow API methods"""

    def _workflow_post(self, endpoint: str, payload: dict[str, Any] | None = None) -> Any:
        response = self._request("POST", endpoint, json=payload or {})
        return self._extract_data(response)

    @overload
    def run_workflow(
        self,
        wid: str,
        input_fields: list[WorkflowInputField],
        output_scope: Literal["all", "output_fields_only"] = "output_fields_only",
        wait_for_completion: Literal[False] = False,
        api_key_type: Literal["WORKFLOW", "VAPP"] = "WORKFLOW",
        timeout: int = 30,
    ) -> str: ...

    @overload
    def run_workflow(
        self,
        wid: str,
        input_fields: list[WorkflowInputField],
        output_scope: Literal["all", "output_fields_only"] = "output_fields_only",
        wait_for_completion: Literal[True] = True,
        api_key_type: Literal["WORKFLOW", "VAPP"] = "WORKFLOW",
        timeout: int = 30,
    ) -> WorkflowRunResult: ...

    def run_workflow(
        self,
        wid: str,
        input_fields: list[WorkflowInputField],
        output_scope: Literal["all", "output_fields_only"] = "output_fields_only",
        wait_for_completion: bool = False,
        api_key_type: Literal["WORKFLOW", "VAPP"] = "WORKFLOW",
        timeout: int = 30,
    ) -> str | WorkflowRunResult:
        """Run workflow

        Args:
            wid: Workflow ID
            input_fields: Input fields list
            output_scope: Output scope, optional values: 'all' or 'output_fields_only'
            wait_for_completion: Whether to wait for completion
            api_key_type: Key type, optional values: 'WORKFLOW' or 'VAPP'
            timeout: Timeout (seconds)

        Returns:
            Union[str, WorkflowRunResult]: Workflow run ID or run result

        Raises:
            WorkflowError: Workflow run error
            TimeoutError: Timeout error
        """
        payload = {
            "wid": wid,
            "output_scope": output_scope,
            "wait_for_completion": wait_for_completion,
            "input_fields": [{"node_id": field.node_id, "field_name": field.field_name, "value": field.value} for field in input_fields],
        }

        result = self._request("POST", "workflow/run", json=payload, api_key_type=api_key_type)

        if not wait_for_completion:
            return result["data"]["rid"]

        rid = result.get("rid") or (isinstance(result["data"], dict) and result["data"].get("rid")) or ""
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Workflow execution timed out after {timeout} seconds")

            if api_key_type == "WORKFLOW":
                result = self.check_workflow_status(rid, api_key_type=api_key_type)
            else:
                result = self.check_workflow_status(rid, wid=wid, api_key_type=api_key_type)
            if result.status == 200:
                return result
            elif result.status == 500:
                raise WorkflowError(f"Workflow execution failed: {result.msg}")

            time.sleep(5)

    @overload
    def check_workflow_status(self, rid: str, wid: str | None = None, api_key_type: Literal["WORKFLOW"] = "WORKFLOW") -> WorkflowRunResult: ...

    @overload
    def check_workflow_status(self, rid: str, wid: str, api_key_type: Literal["VAPP"] = "VAPP") -> WorkflowRunResult: ...

    def check_workflow_status(self, rid: str, wid: str | None = None, api_key_type: Literal["WORKFLOW", "VAPP"] = "WORKFLOW") -> WorkflowRunResult:
        """Check workflow run status

        Args:
            rid: Workflow run record ID
            wid: Workflow ID, not required, required when api_key_type is 'VAPP'
            api_key_type: Key type, optional values: 'WORKFLOW' or 'VAPP'

        Returns:
            WorkflowRunResult: Workflow run result

        Raises:
            VectorVeinAPIError: Workflow error
        """
        payload = {"rid": rid}
        if api_key_type == "VAPP" and not wid:
            raise VectorVeinAPIError("Workflow ID cannot be empty when api_key_type is 'VAPP'")
        if wid:
            payload["wid"] = wid
        response = self._request("POST", "workflow/check-status", json=payload, api_key_type=api_key_type)
        return self._parse_workflow_result(response, rid)

    def create_workflow(
        self,
        title: str = "New workflow",
        brief: str = "",
        images: list[str] | None = None,
        tags: list[dict[str, str]] | None = None,
        data: dict[str, Any] | None = None,
        language: str = "zh-CN",
        tool_call_data: dict[str, Any] | None = None,
        source_workflow_wid: str | None = None,
    ) -> Workflow:
        """Create a new workflow

        Args:
            title: Workflow title, default is "New workflow"
            brief: Workflow brief description
            images: List of image URLs
            tags: List of workflow tags, each tag should have 'tid' field
            data: Workflow data containing nodes and edges, default is {"nodes": [], "edges": []}
            language: Workflow language, default is "zh-CN"
            tool_call_data: Tool call data
            source_workflow_wid: Source workflow ID for copying

        Returns:
            Workflow: Created workflow information

        Raises:
            VectorVeinAPIError: Workflow creation error
        """
        payload = {
            "title": title,
            "brief": brief,
            "images": images or [],
            "tags": tags or [],
            "data": data or {"nodes": [], "edges": []},
            "language": language,
            "tool_call_data": tool_call_data or {},
        }

        if source_workflow_wid:
            payload["source_workflow_wid"] = source_workflow_wid

        response = self._request("POST", "workflow/create", json=payload)
        return self._create_workflow_response(response)

    def get_workflow(self, wid: str) -> Workflow:
        response = self._request("POST", "workflow/get", json={"wid": wid})
        return self._create_workflow_response(response)

    def list_workflows(
        self,
        page: int = 1,
        page_size: int = 10,
        tags: list[str] | None = None,
        sort_field: str = "update_time",
        sort_order: str = "descend",
        search_text: str | None = None,
        workflow_related: str | None = None,
        need_fast_access: bool | None = None,
        use_in_chrome_extension: bool | None = None,
        client: str | None = None,
    ) -> dict[str, Any]:
        payload = self._build_payload(
            page=page,
            page_size=page_size,
            tags=tags,
            sort_field=sort_field,
            sort_order=sort_order,
            search_text=search_text,
            workflow_related=workflow_related,
            need_fast_access=need_fast_access,
            use_in_chrome_extension=use_in_chrome_extension,
            client=client,
        )
        return self._workflow_post("workflow/list", payload)

    def update_workflow(
        self,
        wid: str,
        data: dict[str, Any],
        title: str | None = None,
        brief: str | None = None,
        images: list[str] | None = None,
        tags: list[str | dict[str, Any]] | None = None,
        language: str | None = None,
        client: str | None = None,
    ) -> dict[str, Any]:
        payload = self._build_payload(
            {"wid": wid, "data": data},
            title=title,
            brief=brief,
            images=images,
            tags=tags,
            language=language,
            client=client,
        )
        return self._workflow_post("workflow/update", payload)

    def update_workflow_tool_call_data(self, wid: str, tool_call_data: dict[str, Any]) -> dict[str, Any]:
        payload = {"wid": wid, "tool_call_data": tool_call_data}
        return self._workflow_post("workflow/update-tool-call-data", payload)

    def delete_workflow(self, wid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/delete", {"wid": wid})

    def run_workflow_template(
        self,
        tid: str,
        data: dict[str, Any],
        run_from: str | None = None,
        accept_subscribe_message: bool | None = None,
    ) -> str:
        payload = self._build_payload(
            {"tid": tid, "data": data},
            run_from=run_from,
            accept_subscribe_message=accept_subscribe_message,
        )
        response_data = self._workflow_post("workflow/run-template", payload)
        return str(response_data.get("rid", ""))

    def resume_workflow_run(self, rid: str, human_feedback_nodes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        payload = self._build_payload({"rid": rid}, human_feedback_nodes=human_feedback_nodes)
        return self._workflow_post("workflow/resume-run", payload)

    def stop_workflow_run(self, rid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/stop-run", {"rid": rid})

    def get_workflow_run_record(self, rid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/run-record/get", {"rid": rid})

    def list_workflow_run_records(
        self,
        page: int = 1,
        page_size: int = 10,
        wid: str | None = None,
        status: list[str] | None = None,
        shared: list[bool] | None = None,
        run_from: list[str] | None = None,
        sort_field: str = "start_time",
        sort_order: str = "descend",
        need_workflow: bool | None = None,
    ) -> dict[str, Any]:
        payload = self._build_payload(
            page=page,
            page_size=page_size,
            wid=wid,
            status=status,
            shared=shared,
            run_from=run_from,
            sort_field=sort_field,
            sort_order=sort_order,
            need_workflow=need_workflow,
        )
        return self._workflow_post("workflow/run-record/list", payload)

    def stop_workflow_run_record(self, rid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/run-record/stop", {"rid": rid})

    def delete_workflow_run_record(self, rid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/run-record/delete", {"rid": rid})

    def list_workflow_run_schedules(
        self,
        page: int = 1,
        page_size: int = 10,
        status: list[str] | None = None,
        sort_field: str = "update_time",
        sort_order: str = "descend",
    ) -> dict[str, Any]:
        payload = self._build_payload(page=page, page_size=page_size, status=status, sort_field=sort_field, sort_order=sort_order)
        return self._workflow_post("workflow/run-schedule/list", payload)

    def get_workflow_run_schedule(self, sid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/run-schedule/get", {"sid": sid})

    def update_workflow_run_schedule(
        self,
        cron_expression: str,
        sid: str | None = None,
        wid: str | None = None,
        timezone: str | None = None,
    ) -> dict[str, Any]:
        payload = self._build_payload(
            cron_expression=cron_expression,
            sid=sid,
            wid=wid,
            timezone=timezone,
        )
        return self._workflow_post("workflow/run-schedule/update", payload)

    def delete_workflow_run_schedule(self, sid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/run-schedule/delete", {"sid": sid})

    def get_workflow_template(self, tid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/template/get", {"tid": tid})

    def update_workflow_template(
        self,
        tid: str,
        data: dict[str, Any],
        title: str | None = None,
        brief: str | None = None,
        images: list[str] | None = None,
        tags: list[str] | None = None,
        agent_only: bool | None = None,
    ) -> dict[str, Any]:
        payload = self._build_payload(
            {"tid": tid, "data": data},
            title=title,
            brief=brief,
            images=images,
            tags=tags,
            agent_only=agent_only,
        )
        return self._workflow_post("workflow/template/update", payload)

    def update_workflow_template_tool_call_data(self, tid: str, tool_call_data: dict[str, Any]) -> dict[str, Any]:
        return self._workflow_post("workflow/template/update-tool-call-data", {"tid": tid, "tool_call_data": tool_call_data})

    def create_workflow_template(self, wid: str, **payload: Any) -> dict[str, Any]:
        request_data = {"wid": wid, **payload}
        return self._workflow_post("workflow/template/create", request_data)

    def list_workflow_templates(self, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/template/list", payload)

    def delete_workflow_template(self, tid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/template/delete", {"tid": tid})

    def add_workflow_template(self, tid: str, **payload: Any) -> dict[str, Any]:
        request_data = {"tid": tid, **payload}
        return self._workflow_post("workflow/template/add", request_data)

    def api_download_workflow_template(self, tid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/template/api-download", {"tid": tid})

    def create_workflow_tag(self, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/tag/create", payload)

    def delete_workflow_tag(self, tid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/tag/delete", {"tid": tid})

    def list_workflow_tags(self, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/tag/list", payload)

    def update_workflow_tag(self, tid: str, **payload: Any) -> dict[str, Any]:
        request_data = {"tid": tid, **payload}
        return self._workflow_post("workflow/tag/update", request_data)

    def search_workflow_tags(self, keyword: str) -> dict[str, Any]:
        return self._workflow_post("workflow/tag/search", {"keyword": keyword})

    def list_workflow_trash(
        self,
        page: int = 1,
        page_size: int = 10,
        tags: list[str] | None = None,
        sort_field: str = "update_time",
        sort_order: str = "descend",
        search_text: str | None = None,
        client: str | None = None,
    ) -> dict[str, Any]:
        payload = self._build_payload(
            page=page,
            page_size=page_size,
            tags=tags,
            sort_field=sort_field,
            sort_order=sort_order,
            search_text=search_text,
            client=client,
        )
        return self._workflow_post("workflow/trash/list", payload)

    def restore_workflow_from_trash(self, wid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/trash/restore", {"wid": wid})

    def purge_workflow_from_trash(self, wid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/trash/purge", {"wid": wid})

    def add_workflow_fast_access(self, wid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/fast-access/add", {"wid": wid})

    def remove_workflow_fast_access(self, wid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/fast-access/delete", {"wid": wid})

    def get_workflow_schedule_trigger(self, wid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/schedule-trigger/get", {"wid": wid})

    def update_workflow_schedule_trigger(self, wid: str, data: dict[str, Any], timezone: str | None = None) -> dict[str, Any]:
        payload = self._build_payload({"wid": wid, "data": data}, timezone=timezone)
        return self._workflow_post("workflow/schedule-trigger/update", payload)

    def delete_workflow_schedule_trigger(self, wid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/schedule-trigger/delete", {"wid": wid})

    def check_vector_database_access(self, vid: str, access_type: str = "read") -> dict[str, Any]:
        return self._workflow_post("workflow/vector-database/check-access", {"vid": vid, "access_type": access_type})

    def get_vector_database(self, vid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/vector-database/get", {"vid": vid})

    def update_vector_database(self, vid: str, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/vector-database/update", {"vid": vid, **payload})

    def create_vector_database(self, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/vector-database/create", payload)

    def list_vector_databases(self, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/vector-database/list", payload)

    def delete_vector_database(self, vid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/vector-database/delete", {"vid": vid})

    def get_vector_database_object(self, oid: str, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/vector-database-object/get", {"oid": oid, **payload})

    def batch_get_vector_database_objects(self, database_vid: str, oids: list[str], **payload: Any) -> dict[str, Any]:
        return self._workflow_post(
            "workflow/vector-database-object/batch-get",
            {"database_vid": database_vid, "oids": oids, **payload},
        )

    def update_vector_database_object(self, oid: str, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/vector-database-object/update", {"oid": oid, **payload})

    def create_vector_database_object(self, vid: str, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/vector-database-object/create", {"vid": vid, **payload})

    def list_vector_database_objects(self, vid: str, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/vector-database-object/list", {"vid": vid, **payload})

    def delete_vector_database_object(self, oid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/vector-database-object/delete", {"oid": oid})

    def get_vector_database_object_segment(self, oid: str, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/vector-database-object-segment/get", {"oid": oid, **payload})

    def update_vector_database_object_segment(self, sid: str, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/vector-database-object-segment/update", {"sid": sid, **payload})

    def list_vector_database_object_segments(self, oid: str, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/vector-database-object-segment/list", {"oid": oid, **payload})

    def delete_vector_database_object_segment(self, oid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/vector-database-object-segment/delete", {"oid": oid})

    def get_relational_database(self, rid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/relational-database/get", {"rid": rid})

    def update_relational_database(self, rid: str, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/relational-database/update", {"rid": rid, **payload})

    def create_relational_database(self, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/relational-database/create", payload)

    def list_relational_databases(self, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/relational-database/list", payload)

    def delete_relational_database(self, rid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/relational-database/delete", {"rid": rid})

    def refresh_relational_database(self, rid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/relational-database/refresh", {"rid": rid})

    def run_sql_on_relational_database(self, rid: str, sql: str) -> dict[str, Any]:
        return self._workflow_post("workflow/relational-database/run-sql", {"rid": rid, "sql": sql})

    def get_relational_database_table(self, tid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/relational-database-table/get", {"tid": tid})

    def update_relational_database_table(self, tid: str, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/relational-database-table/update", {"tid": tid, **payload})

    def refresh_relational_database_table(self, tid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/relational-database-table/refresh", {"tid": tid})

    def create_relational_database_table(
        self,
        rid: str,
        add_method: str,
        files: list[str],
        sql_statement: str,
        table_schema: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return self._workflow_post(
            "workflow/relational-database-table/create",
            {
                "rid": rid,
                "add_method": add_method,
                "files": files,
                "sql_statement": sql_statement,
                "table_schema": table_schema,
            },
        )

    def list_relational_database_tables(self, rid: str, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/relational-database-table/list", {"rid": rid, **payload})

    def delete_relational_database_table(self, tid: str) -> dict[str, Any]:
        return self._workflow_post("workflow/relational-database-table/delete", {"tid": tid})

    def get_relational_database_table_schema(self, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/relational-database-task/get-table-schema", payload)

    def refresh_relational_database_table_max_rows(self, rid: str | None = None, tid: str | None = None) -> dict[str, Any]:
        payload = self._build_payload(rid=rid, tid=tid)
        return self._workflow_post("workflow/relational-database-task/refresh-table-max-rows", payload)

    def list_relational_database_table_records(self, tid: str, **payload: Any) -> dict[str, Any]:
        return self._workflow_post("workflow/relational-database-table-record/list", {"tid": tid, **payload})

    def update_relational_database_table_records(self, tid: str, records: list[dict[str, Any]]) -> dict[str, Any]:
        return self._workflow_post("workflow/relational-database-table-record/update", {"tid": tid, "records": records})

    def delete_relational_database_table_records(self, tid: str, records: list[dict[str, Any]]) -> dict[str, Any]:
        return self._workflow_post("workflow/relational-database-table-record/delete", {"tid": tid, "records": records})

    def add_relational_database_table_record(
        self,
        tid: str,
        add_method: str,
        record: dict[str, Any] | None = None,
        file: str | None = None,
    ) -> dict[str, Any]:
        payload = self._build_payload({"tid": tid, "add_method": add_method}, record=record, file=file)
        return self._workflow_post("workflow/relational-database-table-record/add", payload)


class WorkflowAsyncMixin(WorkflowMixin):
    """Asynchronous workflow API methods"""

    async def _workflow_post(self, endpoint: str, payload: dict[str, Any] | None = None) -> Any:
        response = await self._request("POST", endpoint, json=payload or {})
        return self._extract_data(response)

    @overload
    async def run_workflow(
        self,
        wid: str,
        input_fields: list[WorkflowInputField],
        output_scope: Literal["all", "output_fields_only"] = "output_fields_only",
        wait_for_completion: Literal[False] = False,
        api_key_type: Literal["WORKFLOW", "VAPP"] = "WORKFLOW",
        timeout: int = 30,
    ) -> str: ...

    @overload
    async def run_workflow(
        self,
        wid: str,
        input_fields: list[WorkflowInputField],
        output_scope: Literal["all", "output_fields_only"] = "output_fields_only",
        wait_for_completion: Literal[True] = True,
        api_key_type: Literal["WORKFLOW", "VAPP"] = "WORKFLOW",
        timeout: int = 30,
    ) -> WorkflowRunResult: ...

    async def run_workflow(
        self,
        wid: str,
        input_fields: list[WorkflowInputField],
        output_scope: Literal["all", "output_fields_only"] = "output_fields_only",
        wait_for_completion: bool = False,
        api_key_type: Literal["WORKFLOW", "VAPP"] = "WORKFLOW",
        timeout: int = 30,
    ) -> str | WorkflowRunResult:
        """Async run workflow

        Args:
            wid: Workflow ID
            input_fields: Input field list
            output_scope: Output scope, optional values: 'all' or 'output_fields_only'
            wait_for_completion: Whether to wait for completion
            api_key_type: Key type, optional values: 'WORKFLOW' or 'VAPP'
            timeout: Timeout (seconds)

        Returns:
            Union[str, WorkflowRunResult]: Workflow run ID or run result

        Raises:
            WorkflowError: Workflow run error
            TimeoutError: Timeout error
        """
        payload = {
            "wid": wid,
            "output_scope": output_scope,
            "wait_for_completion": wait_for_completion,
            "input_fields": [{"node_id": field.node_id, "field_name": field.field_name, "value": field.value} for field in input_fields],
        }

        result = await self._request("POST", "workflow/run", json=payload, api_key_type=api_key_type)

        if not wait_for_completion:
            return result["data"]["rid"]

        rid = result.get("rid") or (isinstance(result["data"], dict) and result["data"].get("rid")) or ""
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Workflow execution timed out after {timeout} seconds")

            if api_key_type == "WORKFLOW":
                result = await self.check_workflow_status(rid, api_key_type=api_key_type)
            else:
                result = await self.check_workflow_status(rid, wid=wid, api_key_type=api_key_type)
            if result.status == 200:
                return result
            elif result.status == 500:
                raise WorkflowError(f"Workflow execution failed: {result.msg}")

            await asyncio.sleep(5)

    @overload
    async def check_workflow_status(self, rid: str, wid: str | None = None, api_key_type: Literal["WORKFLOW"] = "WORKFLOW") -> WorkflowRunResult: ...

    @overload
    async def check_workflow_status(self, rid: str, wid: str, api_key_type: Literal["VAPP"] = "VAPP") -> WorkflowRunResult: ...

    async def check_workflow_status(self, rid: str, wid: str | None = None, api_key_type: Literal["WORKFLOW", "VAPP"] = "WORKFLOW") -> WorkflowRunResult:
        """Async check workflow run status

        Args:
            rid: Workflow run record ID
            wid: Workflow ID, required when api_key_type is 'VAPP'
            api_key_type: Key type, optional values: 'WORKFLOW' or 'VAPP'

        Raises:
            VectorVeinAPIError: Workflow error
        """
        payload = {"rid": rid}
        if api_key_type == "VAPP" and not wid:
            raise VectorVeinAPIError("Workflow ID cannot be empty when api_key_type is 'VAPP'")
        if wid:
            payload["wid"] = wid
        response = await self._request("POST", "workflow/check-status", json=payload, api_key_type=api_key_type)
        return self._parse_workflow_result(response, rid)

    async def create_workflow(
        self,
        title: str = "New workflow",
        brief: str = "",
        images: list[str] | None = None,
        tags: list[dict[str, str]] | None = None,
        data: dict[str, Any] | None = None,
        language: str = "zh-CN",
        tool_call_data: dict[str, Any] | None = None,
        source_workflow_wid: str | None = None,
    ) -> Workflow:
        """Async create a new workflow

        Args:
            title: Workflow title, default is "New workflow"
            brief: Workflow brief description
            images: List of image URLs
            tags: List of workflow tags, each tag should have 'tid' field
            data: Workflow data containing nodes and edges, default is {"nodes": [], "edges": []}
            language: Workflow language, default is "zh-CN"
            tool_call_data: Tool call data
            source_workflow_wid: Source workflow ID for copying

        Returns:
            Workflow: Created workflow information

        Raises:
            VectorVeinAPIError: Workflow creation error
        """
        payload = {
            "title": title,
            "brief": brief,
            "images": images or [],
            "tags": tags or [],
            "data": data or {"nodes": [], "edges": []},
            "language": language,
            "tool_call_data": tool_call_data or {},
        }

        if source_workflow_wid:
            payload["source_workflow_wid"] = source_workflow_wid

        response = await self._request("POST", "workflow/create", json=payload)
        return self._create_workflow_response(response)

    async def get_workflow(self, wid: str) -> Workflow:
        response = await self._request("POST", "workflow/get", json={"wid": wid})
        return self._create_workflow_response(response)

    async def list_workflows(
        self,
        page: int = 1,
        page_size: int = 10,
        tags: list[str] | None = None,
        sort_field: str = "update_time",
        sort_order: str = "descend",
        search_text: str | None = None,
        workflow_related: str | None = None,
        need_fast_access: bool | None = None,
        use_in_chrome_extension: bool | None = None,
        client: str | None = None,
    ) -> dict[str, Any]:
        payload = self._build_payload(
            page=page,
            page_size=page_size,
            tags=tags,
            sort_field=sort_field,
            sort_order=sort_order,
            search_text=search_text,
            workflow_related=workflow_related,
            need_fast_access=need_fast_access,
            use_in_chrome_extension=use_in_chrome_extension,
            client=client,
        )
        return await self._workflow_post("workflow/list", payload)

    async def update_workflow(
        self,
        wid: str,
        data: dict[str, Any],
        title: str | None = None,
        brief: str | None = None,
        images: list[str] | None = None,
        tags: list[str | dict[str, Any]] | None = None,
        language: str | None = None,
        client: str | None = None,
    ) -> dict[str, Any]:
        payload = self._build_payload(
            {"wid": wid, "data": data},
            title=title,
            brief=brief,
            images=images,
            tags=tags,
            language=language,
            client=client,
        )
        return await self._workflow_post("workflow/update", payload)

    async def update_workflow_tool_call_data(self, wid: str, tool_call_data: dict[str, Any]) -> dict[str, Any]:
        payload = {"wid": wid, "tool_call_data": tool_call_data}
        return await self._workflow_post("workflow/update-tool-call-data", payload)

    async def delete_workflow(self, wid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/delete", {"wid": wid})

    async def run_workflow_template(
        self,
        tid: str,
        data: dict[str, Any],
        run_from: str | None = None,
        accept_subscribe_message: bool | None = None,
    ) -> str:
        payload = self._build_payload(
            {"tid": tid, "data": data},
            run_from=run_from,
            accept_subscribe_message=accept_subscribe_message,
        )
        response_data = await self._workflow_post("workflow/run-template", payload)
        return str(response_data.get("rid", ""))

    async def resume_workflow_run(self, rid: str, human_feedback_nodes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        payload = self._build_payload({"rid": rid}, human_feedback_nodes=human_feedback_nodes)
        return await self._workflow_post("workflow/resume-run", payload)

    async def stop_workflow_run(self, rid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/stop-run", {"rid": rid})

    async def get_workflow_run_record(self, rid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/run-record/get", {"rid": rid})

    async def list_workflow_run_records(
        self,
        page: int = 1,
        page_size: int = 10,
        wid: str | None = None,
        status: list[str] | None = None,
        shared: list[bool] | None = None,
        run_from: list[str] | None = None,
        sort_field: str = "start_time",
        sort_order: str = "descend",
        need_workflow: bool | None = None,
    ) -> dict[str, Any]:
        payload = self._build_payload(
            page=page,
            page_size=page_size,
            wid=wid,
            status=status,
            shared=shared,
            run_from=run_from,
            sort_field=sort_field,
            sort_order=sort_order,
            need_workflow=need_workflow,
        )
        return await self._workflow_post("workflow/run-record/list", payload)

    async def stop_workflow_run_record(self, rid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/run-record/stop", {"rid": rid})

    async def delete_workflow_run_record(self, rid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/run-record/delete", {"rid": rid})

    async def list_workflow_run_schedules(
        self,
        page: int = 1,
        page_size: int = 10,
        status: list[str] | None = None,
        sort_field: str = "update_time",
        sort_order: str = "descend",
    ) -> dict[str, Any]:
        payload = self._build_payload(page=page, page_size=page_size, status=status, sort_field=sort_field, sort_order=sort_order)
        return await self._workflow_post("workflow/run-schedule/list", payload)

    async def get_workflow_run_schedule(self, sid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/run-schedule/get", {"sid": sid})

    async def update_workflow_run_schedule(
        self,
        cron_expression: str,
        sid: str | None = None,
        wid: str | None = None,
        timezone: str | None = None,
    ) -> dict[str, Any]:
        payload = self._build_payload(
            cron_expression=cron_expression,
            sid=sid,
            wid=wid,
            timezone=timezone,
        )
        return await self._workflow_post("workflow/run-schedule/update", payload)

    async def delete_workflow_run_schedule(self, sid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/run-schedule/delete", {"sid": sid})

    async def get_workflow_template(self, tid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/template/get", {"tid": tid})

    async def update_workflow_template(
        self,
        tid: str,
        data: dict[str, Any],
        title: str | None = None,
        brief: str | None = None,
        images: list[str] | None = None,
        tags: list[str] | None = None,
        agent_only: bool | None = None,
    ) -> dict[str, Any]:
        payload = self._build_payload(
            {"tid": tid, "data": data},
            title=title,
            brief=brief,
            images=images,
            tags=tags,
            agent_only=agent_only,
        )
        return await self._workflow_post("workflow/template/update", payload)

    async def update_workflow_template_tool_call_data(self, tid: str, tool_call_data: dict[str, Any]) -> dict[str, Any]:
        return await self._workflow_post("workflow/template/update-tool-call-data", {"tid": tid, "tool_call_data": tool_call_data})

    async def create_workflow_template(self, wid: str, **payload: Any) -> dict[str, Any]:
        request_data = {"wid": wid, **payload}
        return await self._workflow_post("workflow/template/create", request_data)

    async def list_workflow_templates(self, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/template/list", payload)

    async def delete_workflow_template(self, tid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/template/delete", {"tid": tid})

    async def add_workflow_template(self, tid: str, **payload: Any) -> dict[str, Any]:
        request_data = {"tid": tid, **payload}
        return await self._workflow_post("workflow/template/add", request_data)

    async def api_download_workflow_template(self, tid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/template/api-download", {"tid": tid})

    async def create_workflow_tag(self, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/tag/create", payload)

    async def delete_workflow_tag(self, tid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/tag/delete", {"tid": tid})

    async def list_workflow_tags(self, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/tag/list", payload)

    async def update_workflow_tag(self, tid: str, **payload: Any) -> dict[str, Any]:
        request_data = {"tid": tid, **payload}
        return await self._workflow_post("workflow/tag/update", request_data)

    async def search_workflow_tags(self, keyword: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/tag/search", {"keyword": keyword})

    async def list_workflow_trash(
        self,
        page: int = 1,
        page_size: int = 10,
        tags: list[str] | None = None,
        sort_field: str = "update_time",
        sort_order: str = "descend",
        search_text: str | None = None,
        client: str | None = None,
    ) -> dict[str, Any]:
        payload = self._build_payload(
            page=page,
            page_size=page_size,
            tags=tags,
            sort_field=sort_field,
            sort_order=sort_order,
            search_text=search_text,
            client=client,
        )
        return await self._workflow_post("workflow/trash/list", payload)

    async def restore_workflow_from_trash(self, wid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/trash/restore", {"wid": wid})

    async def purge_workflow_from_trash(self, wid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/trash/purge", {"wid": wid})

    async def add_workflow_fast_access(self, wid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/fast-access/add", {"wid": wid})

    async def remove_workflow_fast_access(self, wid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/fast-access/delete", {"wid": wid})

    async def get_workflow_schedule_trigger(self, wid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/schedule-trigger/get", {"wid": wid})

    async def update_workflow_schedule_trigger(self, wid: str, data: dict[str, Any], timezone: str | None = None) -> dict[str, Any]:
        payload = self._build_payload({"wid": wid, "data": data}, timezone=timezone)
        return await self._workflow_post("workflow/schedule-trigger/update", payload)

    async def delete_workflow_schedule_trigger(self, wid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/schedule-trigger/delete", {"wid": wid})

    async def check_vector_database_access(self, vid: str, access_type: str = "read") -> dict[str, Any]:
        return await self._workflow_post("workflow/vector-database/check-access", {"vid": vid, "access_type": access_type})

    async def get_vector_database(self, vid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/vector-database/get", {"vid": vid})

    async def update_vector_database(self, vid: str, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/vector-database/update", {"vid": vid, **payload})

    async def create_vector_database(self, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/vector-database/create", payload)

    async def list_vector_databases(self, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/vector-database/list", payload)

    async def delete_vector_database(self, vid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/vector-database/delete", {"vid": vid})

    async def get_vector_database_object(self, oid: str, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/vector-database-object/get", {"oid": oid, **payload})

    async def batch_get_vector_database_objects(self, database_vid: str, oids: list[str], **payload: Any) -> dict[str, Any]:
        return await self._workflow_post(
            "workflow/vector-database-object/batch-get",
            {"database_vid": database_vid, "oids": oids, **payload},
        )

    async def update_vector_database_object(self, oid: str, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/vector-database-object/update", {"oid": oid, **payload})

    async def create_vector_database_object(self, vid: str, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/vector-database-object/create", {"vid": vid, **payload})

    async def list_vector_database_objects(self, vid: str, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/vector-database-object/list", {"vid": vid, **payload})

    async def delete_vector_database_object(self, oid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/vector-database-object/delete", {"oid": oid})

    async def get_vector_database_object_segment(self, oid: str, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/vector-database-object-segment/get", {"oid": oid, **payload})

    async def update_vector_database_object_segment(self, sid: str, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/vector-database-object-segment/update", {"sid": sid, **payload})

    async def list_vector_database_object_segments(self, oid: str, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/vector-database-object-segment/list", {"oid": oid, **payload})

    async def delete_vector_database_object_segment(self, oid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/vector-database-object-segment/delete", {"oid": oid})

    async def get_relational_database(self, rid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/relational-database/get", {"rid": rid})

    async def update_relational_database(self, rid: str, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/relational-database/update", {"rid": rid, **payload})

    async def create_relational_database(self, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/relational-database/create", payload)

    async def list_relational_databases(self, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/relational-database/list", payload)

    async def delete_relational_database(self, rid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/relational-database/delete", {"rid": rid})

    async def refresh_relational_database(self, rid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/relational-database/refresh", {"rid": rid})

    async def run_sql_on_relational_database(self, rid: str, sql: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/relational-database/run-sql", {"rid": rid, "sql": sql})

    async def get_relational_database_table(self, tid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/relational-database-table/get", {"tid": tid})

    async def update_relational_database_table(self, tid: str, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/relational-database-table/update", {"tid": tid, **payload})

    async def refresh_relational_database_table(self, tid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/relational-database-table/refresh", {"tid": tid})

    async def create_relational_database_table(
        self,
        rid: str,
        add_method: str,
        files: list[str],
        sql_statement: str,
        table_schema: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return await self._workflow_post(
            "workflow/relational-database-table/create",
            {
                "rid": rid,
                "add_method": add_method,
                "files": files,
                "sql_statement": sql_statement,
                "table_schema": table_schema,
            },
        )

    async def list_relational_database_tables(self, rid: str, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/relational-database-table/list", {"rid": rid, **payload})

    async def delete_relational_database_table(self, tid: str) -> dict[str, Any]:
        return await self._workflow_post("workflow/relational-database-table/delete", {"tid": tid})

    async def get_relational_database_table_schema(self, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/relational-database-task/get-table-schema", payload)

    async def refresh_relational_database_table_max_rows(self, rid: str | None = None, tid: str | None = None) -> dict[str, Any]:
        payload = self._build_payload(rid=rid, tid=tid)
        return await self._workflow_post("workflow/relational-database-task/refresh-table-max-rows", payload)

    async def list_relational_database_table_records(self, tid: str, **payload: Any) -> dict[str, Any]:
        return await self._workflow_post("workflow/relational-database-table-record/list", {"tid": tid, **payload})

    async def update_relational_database_table_records(self, tid: str, records: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._workflow_post("workflow/relational-database-table-record/update", {"tid": tid, "records": records})

    async def delete_relational_database_table_records(self, tid: str, records: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._workflow_post("workflow/relational-database-table-record/delete", {"tid": tid, "records": records})

    async def add_relational_database_table_record(
        self,
        tid: str,
        add_method: str,
        record: dict[str, Any] | None = None,
        file: str | None = None,
    ) -> dict[str, Any]:
        payload = self._build_payload({"tid": tid, "add_method": add_method}, record=record, file=file)
        return await self._workflow_post("workflow/relational-database-table-record/add", payload)
