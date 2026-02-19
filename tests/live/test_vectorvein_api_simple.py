"""VectorVein API simple live tests (sync + async)."""

import pytest

from vectorvein.api import (
    VectorVeinClient,
    AsyncVectorVeinClient,
    WorkflowInputField,
)
from tests.live.live_common import load_live_settings


@pytest.fixture(scope="module")
def settings():
    return load_live_settings()


INPUT_FIELDS = [
    WorkflowInputField(node_id="4669bbbf-0ca4-4844-bc70-c84dbddc7fc2", field_name="search_text", value="清华创客"),
    WorkflowInputField(node_id="4669bbbf-0ca4-4844-bc70-c84dbddc7fc2", field_name="search_engine", value="bing"),
    WorkflowInputField(node_id="4669bbbf-0ca4-4844-bc70-c84dbddc7fc2", field_name="count", value=10),
    WorkflowInputField(node_id="4669bbbf-0ca4-4844-bc70-c84dbddc7fc2", field_name="offset", value=0),
    WorkflowInputField(node_id="4669bbbf-0ca4-4844-bc70-c84dbddc7fc2", field_name="freshness", value="custom"),
    WorkflowInputField(node_id="4669bbbf-0ca4-4844-bc70-c84dbddc7fc2", field_name="custom_freshness", value=""),
]


def test_sync_workflow(settings):
    client = VectorVeinClient(api_key=settings["api_key"], base_url=settings["base_url"])
    workflow_result = client.run_workflow(
        wid=settings["workflow_id"], input_fields=INPUT_FIELDS, wait_for_completion=True, timeout=300
    )
    assert workflow_result is not None


@pytest.mark.asyncio
async def test_async_workflow(settings):
    client = AsyncVectorVeinClient(api_key=settings["vpp_api_key"], base_url=settings["base_url"])
    workflow_result = await client.run_workflow(
        wid=settings["vapp_id"], input_fields=INPUT_FIELDS, wait_for_completion=True, api_key_type="VAPP", timeout=300
    )
    assert workflow_result is not None
