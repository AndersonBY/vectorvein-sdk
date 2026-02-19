from pathlib import Path

from vectorvein.workflow.utils.json_to_code import generate_python_code


WORKFLOW_JSON_PATH = Path(__file__).resolve().parent.parent / "workflow.json"


def test_workflow_json_to_code():
    """Generate Python code from workflow.json and verify it is non-empty."""
    code = generate_python_code(json_file=WORKFLOW_JSON_PATH)

    assert code, "Generated code should not be empty"
    assert "import" in code or "from" in code, "Generated code should contain import statements"
