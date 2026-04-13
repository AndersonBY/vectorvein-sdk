import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from vectorvein.cli._parser_builder import build_parser
from vectorvein.cli.main import main as cli_main


def _read_output(capsys: pytest.CaptureFixture[str]) -> tuple[str, str]:
    captured = capsys.readouterr()
    return captured.out, captured.err


def test_task_agent_help_shows_group_navigation(capsys: pytest.CaptureFixture[str]):
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["task-agent", "-h"])

    out = capsys.readouterr().out
    assert "Manage reusable agents, tasks, cycles, skills, memory, and related task-agent resources." in out
    assert "Create, inspect, update, duplicate, and favorite reusable agents." in out
    assert "Create, inspect, control, and share agent tasks." in out
    assert "Organize agents into reusable collections." in out
    assert "Register, inspect, and test MCP servers." in out
    assert "Publish workflows as reusable tools." in out
    assert "Manage recurring agent task schedules." in out
    assert "Examples:" in out
    assert "vectorvein task-agent agent create --name" in out
    assert "vectorvein task-agent task create --agent-id" in out


def test_task_agent_missing_subgroup_suggests_valid_paths(capsys: pytest.CaptureFixture[str]):
    exit_code = cli_main(["task-agent", "create"])
    stdout, stderr = _read_output(capsys)

    assert exit_code == 2
    assert stdout == ""
    assert "task-agent requires a subgroup before an action." in stderr
    assert "vectorvein task-agent agent create --name 'My Agent'" in stderr
    assert "vectorvein task-agent task create --agent-id agent_xxx --text 'Do work'" in stderr
    assert "vectorvein task-agent -h" in stderr


def test_task_agent_missing_subgroup_json_error_contains_suggestions(capsys: pytest.CaptureFixture[str]):
    exit_code = cli_main(["--format", "json", "task-agent", "create"])
    stdout, stderr = _read_output(capsys)

    assert exit_code == 2
    assert stdout == ""
    payload = json.loads(stderr)
    assert payload["ok"] is False
    assert payload["error"]["type"] == "usage_error"
    assert payload["error"]["message"] == "task-agent requires a subgroup before an action."
    assert payload["error"]["expected_command"] == "vectorvein task-agent <group> <action> [options]"
    assert payload["error"]["suggestions"] == [
        "vectorvein task-agent agent create --name 'My Agent'",
        "vectorvein task-agent task create --agent-id agent_xxx --text 'Do work'",
        "vectorvein task-agent -h",
    ]
    assert payload["error"]["example"] == "vectorvein task-agent agent create --name 'Research Assistant'"
