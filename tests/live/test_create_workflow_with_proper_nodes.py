"""VectorVein API create_workflow with proper node builder (live)."""

import pytest

from vectorvein.api import VectorVeinClient, Workflow
from vectorvein.workflow.graph.workflow import Workflow as WorkflowBuilder
from vectorvein.workflow.nodes import TextInOut, TemplateCompose, OpenAI, Text
from tests.live.live_common import load_live_settings


@pytest.fixture(scope="module")
def settings():
    return load_live_settings()


@pytest.fixture
def client(settings):
    return VectorVeinClient(api_key=settings["api_key"], base_url=settings["base_url"])


def test_create_workflow_with_proper_nodes(client):
    """Create a workflow using the node builder and push it via API."""
    wb = WorkflowBuilder()

    text_input = TextInOut("text_input_1")
    text_input.ports["text"].value = "请为我写一个关于AI的小故事"

    template_node = TemplateCompose("template_1")
    template_node.ports["template"].value = "用户请求: {{user_input}}\n\n请创作一个有趣的故事。"
    template_node.add_port("user_input", "text", value="", is_output=False)

    llm_node = OpenAI("llm_1")
    llm_node.ports["llm_model"].value = "gpt-4"
    llm_node.ports["temperature"].value = 0.7
    llm_node.ports["top_p"].value = 0.9

    output_node = Text("output_1")

    wb.add_nodes([text_input, template_node, llm_node, output_node])
    wb.connect(text_input, "output", template_node, "user_input")
    wb.connect(template_node, "output", llm_node, "prompt")
    wb.connect(llm_node, "output", output_node, "text")
    wb.layout({"direction": "LR", "node_spacing": 300, "layer_spacing": 200})

    workflow_data = wb.to_dict()
    check_result = wb.check()
    assert check_result["no_cycle"]
    assert check_result["no_isolated_nodes"]
    assert len(workflow_data["nodes"]) == 4
    assert len(workflow_data["edges"]) == 3

    api_workflow = client.create_workflow(
        title="AI故事生成工作流",
        brief="使用模板和GPT-4生成AI相关故事的完整工作流",
        data=workflow_data,
        language="zh-CN",
    )

    assert isinstance(api_workflow, Workflow)
    assert api_workflow.wid is not None
    assert len(api_workflow.data.get("nodes", [])) == 4
    assert len(api_workflow.data.get("edges", [])) == 3


def test_create_text_processing_workflow(client):
    """Create a text-processing workflow with splitter nodes."""
    from vectorvein.workflow.nodes import TextSplitters, RegexExtract, ListRender

    wb = WorkflowBuilder()

    text_input = TextInOut("text_input")
    text_input.ports["text"].value = "这是一段长文本。需要分割处理。包含多个句子。"

    splitter = TextSplitters("splitter")
    splitter.ports["split_method"].value = "delimiter"
    splitter.ports["delimiter"].value = "。"

    regex_extract = RegexExtract("regex")
    regex_extract.ports["pattern"].value = r"^\s*(.+)\s*$"
    regex_extract.ports["first_match"].value = False

    list_render = ListRender("renderer")
    list_render.ports["separator"].value = "\n- "
    list_render.ports["output_type"].value = "text"

    output = Text("output")

    wb.add_nodes([text_input, splitter, regex_extract, list_render, output])
    wb.connect(text_input, "output", splitter, "text")
    wb.connect(splitter, "output", regex_extract, "text")
    wb.connect(regex_extract, "output", list_render, "list")
    wb.connect(list_render, "output", output, "text")
    wb.layout({"direction": "TB", "node_spacing": 150, "layer_spacing": 200})

    workflow_data = wb.to_dict()
    assert len(workflow_data["nodes"]) == 5
    assert len(workflow_data["edges"]) == 4

    api_workflow = client.create_workflow(
        title="文本分割与处理工作流",
        brief="将长文本分割成句子并格式化输出",
        data=workflow_data,
        language="zh-CN",
    )

    assert len(api_workflow.data.get("nodes", [])) == 5
    assert len(api_workflow.data.get("edges", [])) == 4
