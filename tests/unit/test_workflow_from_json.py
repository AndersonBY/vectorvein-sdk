from pathlib import Path

from vectorvein.workflow.graph.workflow import Workflow


WORKFLOW_JSON_PATH = Path(__file__).resolve().parent.parent / "workflow.json"


def test_workflow_from_json():
    """Load workflow.json and verify parsed structure."""
    json_str = WORKFLOW_JSON_PATH.read_text(encoding="utf-8")
    workflow = Workflow.from_json(json_str)

    assert workflow.edges, "Workflow should have at least one edge"
    assert len(workflow.nodes) > 0, "Workflow should have at least one node"
