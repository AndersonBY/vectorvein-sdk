from pathlib import Path

from vectorvein.workflow.utils.analyse import analyse_workflow_record, format_workflow_analysis_for_llm


WORKFLOW_JSON_PATH = Path(__file__).resolve().parent.parent / "workflow.json"


def test_workflow_record_analyse():
    """Analyse workflow.json and verify the result structure."""
    workflow_json = WORKFLOW_JSON_PATH.read_text(encoding="utf-8")

    result = analyse_workflow_record(
        workflow_json,
        connected_only=True,
        reserver_programming_function_ports=True,
    )

    assert isinstance(result, dict), "Analysis result should be a dict"
    assert result, "Analysis result should not be empty"


def test_format_workflow_analysis_for_llm():
    """Verify LLM-formatted analysis produces non-empty output."""
    workflow_json = WORKFLOW_JSON_PATH.read_text(encoding="utf-8")

    result = analyse_workflow_record(
        workflow_json,
        connected_only=True,
        reserver_programming_function_ports=True,
    )

    formatted = format_workflow_analysis_for_llm(result, 120)
    assert formatted, "Formatted analysis should not be empty"
    assert isinstance(formatted, str)
