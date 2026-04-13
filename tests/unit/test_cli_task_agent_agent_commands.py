import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from vectorvein.cli._parser_builder import build_parser
from vectorvein.cli.main import main as cli_main


def _read_json_output(capsys: pytest.CaptureFixture[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    captured = capsys.readouterr()
    stdout = json.loads(captured.out) if captured.out.strip() else {}
    stderr = json.loads(captured.err) if captured.err.strip() else {}
    return stdout, stderr


def test_agent_create_help_lists_full_schema(capsys: pytest.CaptureFixture[str]):
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["task-agent", "agent", "create", "-h"])

    out = capsys.readouterr().out
    assert "--usage-hint" in out
    assert "--default-load-user-memory" in out
    assert "--default-compress-memory-after-tokens" in out
    assert "--default-workspace-files" in out
    assert "--default-sub-agent-ids" in out
    assert "--required-skills" in out
    assert "--available-mcp-tool-ids" in out
    assert "--tag-ids" in out
    assert "--is-official" not in out
    assert "--official-order" not in out
    assert "Whether the agent allows interruption by default." in out
    assert "Whether the agent uses a workspace by default." in out
    assert "Whether the agent loads user memory by default." in out
    assert "Whether mounted cloud storage is writable." in out
    assert "Whether the agent is shared." in out
    assert "Whether the agent is publicly visible." in out
    assert "Default: true." in out
    assert "Default: backend default." in out
    assert "Default: false." in out
    assert "JSON object or @file" in out
    assert "Examples:" in out


def test_cli_agent_create_accepts_full_schema(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    captured: dict[str, Any] = {}

    class _FakeClient:
        def __init__(self, api_key: str, base_url: str | None = None):
            self.api_key = api_key
            self.base_url = base_url

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            return False

        def create_agent(self, **kwargs: Any):
            captured.update(kwargs)
            return {"agent_id": "agent_1"}

    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", _FakeClient)

    exit_code = cli_main(
        [
            "--format",
            "json",
            "--api-key",
            "test_key",
            "task-agent",
            "agent",
            "create",
            "--name",
            "Research Assistant",
            "--avatar",
            "https://example.com/avatar.png",
            "--description",
            "Summarize and organize findings.",
            "--system-prompt",
            "You are an analytical assistant.",
            "--usage-hint",
            '{"task_tip":"Summarize weekly research reports"}',
            "--model-name",
            "gpt-4o",
            "--backend-type",
            "openai",
            "--max-cycles",
            "30",
            "--default-allow-interruption",
            "false",
            "--default-use-workspace",
            "true",
            "--default-load-user-memory",
            "true",
            "--default-compress-memory-after-tokens",
            "64000",
            "--default-agent-type",
            "computer",
            "--default-workspace-files",
            '[{"name":"README.md","oss_path":"oss://bucket/readme"}]',
            "--default-sub-agent-ids",
            '["sub_1"]',
            "--required-skills",
            '[{"skill_id":"skill_1","required":true}]',
            "--default-output-verifier",
            "def main(): return '{}'",
            "--default-computer-pod-setting-id",
            "pod_1",
            "--default-cloud-storage-paths",
            '["/documents/reports"]',
            "--default-cloud-storage-write-enabled",
            "true",
            "--available-workflow-ids",
            '["wf_1"]',
            "--available-template-ids",
            '["tpl_1"]',
            "--available-mcp-tool-ids",
            '["tool_1"]',
            "--tag-ids",
            '["tag_1"]',
            "--shared",
            "true",
            "--is-public",
            "false",
        ]
    )
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert stdout["ok"] is True
    assert captured == {
        "name": "Research Assistant",
        "avatar": "https://example.com/avatar.png",
        "description": "Summarize and organize findings.",
        "system_prompt": "You are an analytical assistant.",
        "usage_hint": {"task_tip": "Summarize weekly research reports"},
        "default_model_name": "gpt-4o",
        "default_backend_type": "openai",
        "default_max_cycles": 30,
        "default_allow_interruption": False,
        "default_use_workspace": True,
        "default_load_user_memory": True,
        "default_compress_memory_after_tokens": 64000,
        "default_agent_type": "computer",
        "default_workspace_files": [{"name": "README.md", "oss_path": "oss://bucket/readme"}],
        "default_sub_agent_ids": ["sub_1"],
        "required_skills": [{"skill_id": "skill_1", "required": True}],
        "default_output_verifier": "def main(): return '{}'",
        "default_computer_pod_setting_id": "pod_1",
        "default_cloud_storage_paths": ["/documents/reports"],
        "default_cloud_storage_write_enabled": True,
        "available_workflow_ids": ["wf_1"],
        "available_template_ids": ["tpl_1"],
        "available_mcp_tool_ids": ["tool_1"],
        "tag_ids": ["tag_1"],
        "shared": True,
        "is_public": False,
    }


def test_cli_agent_update_accepts_full_schema(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    captured: dict[str, Any] = {}

    class _FakeClient:
        def __init__(self, api_key: str, base_url: str | None = None):
            self.api_key = api_key
            self.base_url = base_url

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            return False

        def update_agent(self, **kwargs: Any):
            captured.update(kwargs)
            return {"agent_id": "agent_1"}

    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", _FakeClient)

    exit_code = cli_main(
        [
            "--format",
            "json",
            "--api-key",
            "test_key",
            "task-agent",
            "agent",
            "update",
            "--agent-id",
            "agent_1",
            "--name",
            "Research Assistant v2",
            "--default-load-user-memory",
            "false",
            "--default-compress-memory-after-tokens",
            "96000",
            "--default-cloud-storage-write-enabled",
            "false",
            "--available-mcp-tool-ids",
            '["tool_2"]',
            "--tag-ids",
            '["tag_2"]',
            "--shared",
            "false",
            "--is-public",
            "true",
        ]
    )
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert stdout["ok"] is True
    assert captured["agent_id"] == "agent_1"
    assert captured["default_load_user_memory"] is False
    assert captured["default_compress_memory_after_tokens"] == 96000
    assert captured["default_cloud_storage_write_enabled"] is False
    assert captured["available_mcp_tool_ids"] == ["tool_2"]
    assert captured["tag_ids"] == ["tag_2"]
    assert captured["shared"] is False
    assert captured["is_public"] is True


def test_cli_agent_create_reads_system_prompt_from_text_file(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
):
    prompt_file = tmp_path / "agent_system_prompt.md"
    prompt_file.write_text("You are a meticulous invoice assistant.", encoding="utf-8")
    description_file = tmp_path / "agent_description.md"
    description_file.write_text("Sort uploaded invoices and export clean CSV summaries.", encoding="utf-8")
    captured: dict[str, Any] = {}

    class _FakeClient:
        def __init__(self, api_key: str, base_url: str | None = None):
            self.api_key = api_key
            self.base_url = base_url

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            return False

        def create_agent(self, **kwargs: Any):
            captured.update(kwargs)
            return {"agent_id": "agent_1"}

    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", _FakeClient)

    exit_code = cli_main(
        [
            "--format",
            "json",
            "--api-key",
            "test_key",
            "task-agent",
            "agent",
            "create",
            "--name",
            "Research Assistant",
            "--description",
            f"@{description_file}",
            "--system-prompt",
            f"@{prompt_file}",
        ]
    )
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert stdout["ok"] is True
    assert captured["description"] == "Sort uploaded invoices and export clean CSV summaries."
    assert captured["system_prompt"] == "You are a meticulous invoice assistant."


def test_agent_update_help_hides_official_only_fields(capsys: pytest.CaptureFixture[str]):
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["task-agent", "agent", "update", "-h"])

    out = capsys.readouterr().out
    assert "--is-official" not in out
    assert "--official-order" not in out
    assert "Whether the agent is shared." in out
    assert "Whether the agent is publicly visible." in out
    assert "Default: unchanged." in out


def test_agent_group_help_hides_public_list_subcommand(capsys: pytest.CaptureFixture[str]):
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["task-agent", "agent", "-h"])

    out = capsys.readouterr().out
    assert "public-list" not in out
    assert "favorite-list" in out


def test_agent_list_help_shows_public_filters(capsys: pytest.CaptureFixture[str]):
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["task-agent", "agent", "list", "-h"])

    out = capsys.readouterr().out
    assert "--is-public BOOL" in out
    assert "--official BOOL" in out
    assert "Default: not set." in out


def test_cli_agent_list_accepts_public_filters(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    captured: dict[str, Any] = {}

    class _FakeClient:
        def __init__(self, api_key: str, base_url: str | None = None):
            self.api_key = api_key
            self.base_url = base_url

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            return False

        def list_agents(self, **kwargs: Any):
            captured.update(kwargs)
            return {"agents": []}

    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", _FakeClient)

    exit_code = cli_main(
        [
            "--format",
            "json",
            "--api-key",
            "test_key",
            "task-agent",
            "agent",
            "list",
            "--page",
            "2",
            "--page-size",
            "5",
            "--search",
            "public",
            "--is-public",
            "true",
            "--official",
            "true",
        ]
    )
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert stdout["ok"] is True
    assert captured == {
        "page": 2,
        "page_size": 5,
        "search": "public",
        "is_public": True,
        "official": True,
    }


def test_cli_agent_search_accepts_public_filters(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    captured: dict[str, Any] = {}

    class _FakeClient:
        def __init__(self, api_key: str, base_url: str | None = None):
            self.api_key = api_key
            self.base_url = base_url

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            return False

        def list_agents(self, **kwargs: Any):
            captured.update(kwargs)
            return {"agents": []}

    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", _FakeClient)

    exit_code = cli_main(
        [
            "--format",
            "json",
            "--api-key",
            "test_key",
            "task-agent",
            "agent",
            "search",
            "--query",
            "official",
            "--page",
            "3",
            "--page-size",
            "8",
            "--is-public",
            "true",
            "--official",
            "false",
        ]
    )
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert stdout["ok"] is True
    assert captured == {
        "page": 3,
        "page_size": 8,
        "search": "official",
        "is_public": True,
        "official": False,
    }
