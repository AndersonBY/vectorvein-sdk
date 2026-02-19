"""VectorVein API create_workflow integration test (live)."""

import pytest

from vectorvein.api import VectorVeinClient, Workflow
from tests.live.live_common import load_live_settings


@pytest.fixture(scope="module")
def settings():
    return load_live_settings()


@pytest.fixture
def client(settings):
    return VectorVeinClient(api_key=settings["api_key"], base_url=settings["base_url"])


def test_create_basic_workflow(client):
    workflow = client.create_workflow(title="Python SDK 测试工作流", brief="通过 Python SDK 创建的测试工作流", language="zh-CN")

    assert isinstance(workflow, Workflow)
    assert workflow.wid is not None
    assert len(workflow.wid) > 0
    assert workflow.title == "Python SDK 测试工作流"
    assert workflow.brief == "通过 Python SDK 创建的测试工作流"
    assert workflow.language == "zh-CN"


def test_create_complex_workflow(client):
    complex_data = {
        "nodes": [
            {"id": "input_node", "type": "input", "position": {"x": 100, "y": 100}},
            {"id": "output_node", "type": "output", "position": {"x": 300, "y": 100}},
        ],
        "edges": [{"id": "edge_1", "source": "input_node", "target": "output_node"}],
    }

    workflow = client.create_workflow(
        title="复杂数据工作流",
        brief="包含节点和边的复杂工作流",
        data=complex_data,
        images=["https://example.com/test.jpg"],
        tool_call_data={"version": "1.0", "created_by": "python_sdk"},
    )

    assert isinstance(workflow, Workflow)
    assert workflow.wid is not None
    assert len(workflow.data.get("nodes", [])) == 2
    assert len(workflow.data.get("edges", [])) == 1
    assert len(workflow.images) == 1
    assert workflow.tool_call_data is not None


def test_create_default_workflow(client):
    workflow = client.create_workflow()

    assert isinstance(workflow, Workflow)
    assert workflow.wid is not None
    assert workflow.title == "New workflow"
    assert workflow.language == "zh-CN"
