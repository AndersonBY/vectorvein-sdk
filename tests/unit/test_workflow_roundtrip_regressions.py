"""Exercise executable workflow exports, including every shipped node class."""

import ast
import importlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from vectorvein.cli._output import CLIUsageError
from vectorvein.cli._parsers import _collect_uploaded_workflow_input_fields
from vectorvein.workflow.graph.workflow import Workflow
from vectorvein.workflow.graph.edge import Edge
from vectorvein.workflow.nodes.tools import ProgrammingFunction
from vectorvein.workflow.nodes.triggers import ButtonTrigger
from vectorvein.workflow.utils.json_to_code import generate_python_code


def _node_classes():
    for path in sorted((Path(__file__).parents[2] / "src/vectorvein/workflow/nodes").glob("*.py")):
        module = importlib.import_module(f"vectorvein.workflow.nodes.{path.stem}")
        for node in ast.parse(path.read_text()).body:
            if isinstance(node, ast.ClassDef):
                yield pytest.param(getattr(module, node.name), id=f"{path.stem}.{node.name}")


@pytest.mark.parametrize("node_class", list(_node_classes()))
def test_every_node_can_be_serialized_loaded_and_exported(node_class):
    original = node_class()
    workflow = Workflow()
    workflow.add_node(original)
    restored = Workflow.from_json(workflow.to_json())
    assert {name: port.value for name, port in restored.nodes[0].ports.items()} == {name: port.value for name, port in original.ports.items()}
    scope = {}
    exec(generate_python_code(json_str=workflow.to_json(), skip_trigger=False), scope)
    assert {name: port.value for name, port in scope["workflow"].nodes[0].ports.items()} == {name: port.value for name, port in original.ports.items()}


@pytest.mark.parametrize("value", [0, False, "", [], {}, None])
def test_codegen_preserves_falsy_values_and_quoted_port_names(value):
    node = ProgrammingFunction()
    # Use a dynamic input so its name and value both pass through the generator.
    name = "input'quoted"
    node.add_port(name=name, port_type="input", value=value)
    # A default nonempty field also needs to be explicitly reset to a falsy value.
    node.ports["code"].value = value
    workflow = Workflow()
    workflow.add_node(node)
    scope = {}
    exec(generate_python_code(json_str=workflow.to_json()), scope)
    restored = scope["workflow"].nodes[0]
    assert restored.ports[name].value == value
    assert restored.ports["code"].value == value


def test_codegen_omits_edges_of_skipped_trigger():
    trigger = ButtonTrigger()
    node = ProgrammingFunction()
    node.add_port(name="input", port_type="input")
    workflow = Workflow()
    workflow.add_nodes([trigger, node])
    workflow.add_edge(Edge("trigger-edge", trigger.id, "trigger", node.id, "input"))
    scope = {}
    exec(generate_python_code(json_str=workflow.to_json()), scope)
    assert len(scope["workflow"].nodes) == 1
    assert scope["workflow"].edges == []


def test_loading_select_values_uses_serialized_options_first():
    from vectorvein.workflow.nodes.control_flows import Conditional

    workflow = Workflow()
    node = Conditional()
    workflow.add_node(node)
    data = workflow.to_dict()
    name = next(name for name, port in node.ports.items() if port.options)
    data["nodes"][0]["data"]["template"][name].update(options=[{"value": "custom", "label": "Custom"}], value="custom")
    restored = Workflow.from_json(json.dumps(data))
    assert restored.nodes[0].ports[name].value == "custom"


def test_invalid_single_upload_is_rejected_before_any_upload(tmp_path):
    paths = [tmp_path / "a.txt", tmp_path / "b.txt"]
    for path in paths:
        path.write_text("content")
    args = SimpleNamespace(upload_to=[f"node:files:{path}" for path in paths], upload_as="single")
    client = Mock()
    with pytest.raises(CLIUsageError, match="exactly one file"):
        _collect_uploaded_workflow_input_fields(args, client)
    client.upload_file.assert_not_called()


def test_codegen_rejects_unknown_nodes_instead_of_dropping_them():
    with pytest.raises(ValueError, match="Node class not found"):
        generate_python_code(
            json_str=json.dumps({"nodes": [{"id": "node_1", "type": "UnknownNode", "category": "tools", "data": {"task_name": "tools.unknown", "template": {}}}], "edges": []})
        )


def test_port_values_accept_scalar_options_and_reject_unknown_values():
    from vectorvein.workflow.graph.port import InputPort

    port = InputPort("format", "select", options=["text", "json"])
    port.value = "json"
    assert port.value == "json"
    with pytest.raises(ValueError, match="not in Port"):
        port.value = "unknown"


def test_dynamic_output_ports_and_node_flags_survive_json_load():
    from vectorvein.workflow.nodes.control_flows import JsonProcess

    workflow = Workflow()
    node = JsonProcess()
    node.add_port("extra", "text", value="value", is_output=True)
    node.ignored = True
    node.lock = True
    node.shadow = True
    workflow.add_node(node)
    restored = Workflow.from_json(workflow.to_json()).nodes[0]
    assert restored.ports["extra"].value == "value"
    assert restored.can_add_output_ports is True
    assert restored.ignored and restored.lock and restored.shadow
