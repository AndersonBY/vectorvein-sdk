import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from vectorvein.cli.main import main as cli_main


def _read_json_output(capsys: pytest.CaptureFixture[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    captured = capsys.readouterr()
    stdout = json.loads(captured.out) if captured.out.strip() else {}
    stderr = json.loads(captured.err) if captured.err.strip() else {}
    return stdout, stderr


class _RecorderClient:
    def __init__(self, api_key: str, base_url: str | None = None):
        self.api_key = api_key
        self.base_url = base_url
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        return False

    def __getattr__(self, name: str):
        def _method(*args: Any, **kwargs: Any):
            self.calls.append((name, args, kwargs))
            return {"method": name, "args": list(args), "kwargs": kwargs}

        return _method


@pytest.mark.parametrize(
    ("argv", "expected_method", "expected_args", "expected_kwargs"),
    [
        (
            [
                "task-agent",
                "collection",
                "create",
                "--title",
                "Docs Agents",
                "--description",
                "Knowledge-focused assistants",
                "--data",
                '{"shared":true}',
            ],
            "create_agent_collection",
            (),
            {"title": "Docs Agents", "description": "Knowledge-focused assistants", "shared": True},
        ),
        (
            [
                "task-agent",
                "mcp-server",
                "test-connection",
                "--data",
                '{"server_url":"https://example.com"}',
            ],
            "test_mcp_server_connection",
            (),
            {"server_url": "https://example.com"},
        ),
        (
            [
                "task-agent",
                "user-memory",
                "batch-toggle",
                "--memory-ids",
                '["memory_1","memory_2"]',
                "--is-active",
                "true",
            ],
            "batch_toggle_user_memories",
            (["memory_1", "memory_2"], True),
            {},
        ),
        (
            [
                "task-agent",
                "skill",
                "install",
                "--skill-id",
                "skill_1",
                "--agent-id",
                "agent_1",
                "--permission-level",
                "auto",
            ],
            "install_skill",
            (),
            {"skill_id": "skill_1", "agent_id": "agent_1", "permission_level": "auto"},
        ),
        (
            [
                "task-agent",
                "workflow-tool",
                "batch-create",
                "--workflow-wids",
                '["wf_1"]',
                "--template-tids",
                '["tpl_1"]',
                "--category-id",
                "cat_1",
            ],
            "batch_create_workflow_tools",
            (),
            {"workflow_wids": ["wf_1"], "template_tids": ["tpl_1"], "category_id": "cat_1"},
        ),
        (
            [
                "task-agent",
                "task-schedule",
                "update",
                "--cron-expression",
                "0 0 * * *",
                "--agent-id",
                "agent_1",
                "--task-info",
                '{"text":"Daily summary"}',
                "--mounted-cloud-storage-paths",
                '["/reports"]',
                "--send-email",
                "true",
                "--load-user-memory",
                "false",
            ],
            "update_task_schedule",
            (),
            {
                "cron_expression": "0 0 * * *",
                "agent_id": "agent_1",
                "task_info": {"text": "Daily summary"},
                "mounted_cloud_storage_paths": ["/reports"],
                "send_email": True,
                "load_user_memory": False,
            },
        ),
    ],
)
def test_cli_task_agent_ecosystem_commands_map_to_sdk(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    expected_method: str,
    expected_args: tuple[Any, ...],
    expected_kwargs: dict[str, Any],
):
    holder: dict[str, _RecorderClient] = {}

    def _factory(api_key: str, base_url: str | None = None):
        client = _RecorderClient(api_key=api_key, base_url=base_url)
        holder["client"] = client
        return client

    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", _factory)

    exit_code = cli_main(["--format", "json", "--api-key", "test_key", *argv])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert stdout["ok"] is True
    assert holder["client"].calls == [(expected_method, expected_args, expected_kwargs)]


def test_cli_skill_upload_and_parse_uses_file_path(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path):
    holder: dict[str, _RecorderClient] = {}

    def _factory(api_key: str, base_url: str | None = None):
        client = _RecorderClient(api_key=api_key, base_url=base_url)
        holder["client"] = client
        return client

    skill_file = tmp_path / "demo.skill"
    skill_file.write_bytes(b"skill-archive")

    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", _factory)

    exit_code = cli_main(
        [
            "--format",
            "json",
            "--api-key",
            "test_key",
            "task-agent",
            "skill",
            "upload-and-parse",
            "--path",
            str(skill_file),
            "--filename",
            "demo.skill",
        ]
    )
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert stdout["ok"] is True
    assert holder["client"].calls == [("upload_and_parse_skill", (str(skill_file),), {"filename": "demo.skill"})]
