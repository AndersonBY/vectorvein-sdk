import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from vectorvein.api import APIKeyError
from vectorvein.cli.main import main as cli_main


def _read_output(capsys: pytest.CaptureFixture[str]) -> tuple[str, str]:
    captured = capsys.readouterr()
    return captured.out, captured.err


def _read_json_output(capsys: pytest.CaptureFixture[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    stdout_text, stderr_text = _read_output(capsys)
    stdout = json.loads(stdout_text) if stdout_text.strip() else {}
    stderr = json.loads(stderr_text) if stderr_text.strip() else {}
    return stdout, stderr


def test_cli_auth_whoami_success_prefers_flag_api_key(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    captured_init: dict[str, str | None] = {}

    class _FakeClient:
        def __init__(self, api_key: str, base_url: str | None = None):
            captured_init["api_key"] = api_key
            captured_init["base_url"] = base_url

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            return False

        @staticmethod
        def get_user_info():
            return {
                "uid": "uid_1",
                "username": "tester",
                "email": "tester@example.com",
                "credits": 42,
                "date_joined": "1710000000000",
            }

    monkeypatch.setenv("VECTORVEIN_API_KEY", "env_key_should_not_win")
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", _FakeClient)

    exit_code = cli_main(["--format", "json", "--api-key", "flag_key", "auth", "whoami"])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert captured_init["api_key"] == "flag_key"
    assert stdout["ok"] is True
    assert stdout["command"] == "auth whoami"
    assert stdout["data"] == {
        "uid": "uid_1",
        "username": "tester",
        "email": "tester@example.com",
        "credits": 42,
        "date_joined": "1710000000000",
    }


def test_cli_missing_api_key_returns_usage_error(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    monkeypatch.delenv("VECTORVEIN_API_KEY", raising=False)

    exit_code = cli_main(["auth", "whoami"])
    stdout, stderr = _read_output(capsys)

    assert exit_code == 2
    assert stdout == ""
    assert "Error [usage_error]" in stderr
    assert "Missing API key" in stderr


def test_cli_workflow_run_accepts_mixed_input_sources(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path):
    inputs_file = tmp_path / "inputs.json"
    inputs_file.write_text(
        json.dumps(
            [
                {"node_id": "node_from_file", "field_name": "text", "value": "hello from file"},
            ]
        ),
        encoding="utf-8",
    )

    captured_run: dict[str, Any] = {}

    class _FakeClient:
        def __init__(self, api_key: str, base_url: str | None = None):
            self.api_key = api_key
            self.base_url = base_url

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            return False

        def run_workflow(self, **kwargs: Any) -> str:
            captured_run.update(kwargs)
            return "rid_123"

    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", _FakeClient)

    exit_code = cli_main(
        [
            "--format",
            "json",
            "--api-key",
            "test_key",
            "workflow",
            "run",
            "--wid",
            "wf_1",
            "--input-fields",
            f"@{inputs_file}",
            "--input-field",
            '{"node_id":"node_inline","field_name":"lang","value":"zh-CN"}',
        ]
    )
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert stdout["ok"] is True
    assert stdout["data"]["rid"] == "rid_123"
    assert captured_run["wid"] == "wf_1"
    assert len(captured_run["input_fields"]) == 2
    assert captured_run["input_fields"][0].node_id == "node_from_file"
    assert captured_run["input_fields"][1].field_name == "lang"


def test_cli_maps_api_key_error_to_exit_code_3(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    class _FakeClient:
        def __init__(self, api_key: str, base_url: str | None = None):
            self.api_key = api_key
            self.base_url = base_url

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            return False

        @staticmethod
        def get_user_info():
            raise APIKeyError("invalid api key", status_code=401)

    monkeypatch.setenv("VECTORVEIN_API_KEY", "env_key")
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", _FakeClient)

    exit_code = cli_main(["--format", "json", "auth", "whoami"])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 3
    assert stdout == {}
    assert stderr["ok"] is False
    assert stderr["error"]["type"] == "api_key_error"
    assert stderr["error"]["status_code"] == 401


def test_cli_accepts_global_flags_after_subcommand(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    class _FakeClient:
        def __init__(self, api_key: str, base_url: str | None = None):
            self.api_key = api_key
            self.base_url = base_url

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            return False

        @staticmethod
        def list_workflows(**_: Any):
            return {"items": [], "total": 0}

    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", _FakeClient)

    exit_code = cli_main(["workflow", "list", "--format", "json", "--compact", "--api-key", "late_key"])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert stdout["ok"] is True
    assert stdout["command"] == "workflow list"
    assert stdout["data"]["total"] == 0


def test_cli_no_arguments_prints_help(capsys: pytest.CaptureFixture[str]):
    exit_code = cli_main([])
    stdout, stderr = _read_output(capsys)

    assert exit_code == 0
    assert "usage: vectorvein" in stdout
    assert stderr == ""


def test_cli_auth_whoami_text_output_hides_user_id(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    class _FakeClient:
        def __init__(self, api_key: str, base_url: str | None = None):
            self.api_key = api_key
            self.base_url = base_url

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            return False

        @staticmethod
        def get_user_info():
            return {
                "uid": "uid_1",
                "username": "tester",
                "email": "tester@example.com",
                "credits": 99,
                "date_joined": "1710000000000",
            }

    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", _FakeClient)
    exit_code = cli_main(["auth", "whoami", "--api-key", "k"])
    stdout, stderr = _read_output(capsys)

    assert exit_code == 0
    assert "uid: uid_1" in stdout
    assert "credits: 99" in stdout
    assert "user_id" not in stdout
    assert stderr == ""


def test_cli_workflow_list_hides_verbose_fields(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    class _FakeClient:
        def __init__(self, api_key: str, base_url: str | None = None):
            self.api_key = api_key
            self.base_url = base_url

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            return False

        @staticmethod
        def list_workflows(**_: Any):
            return {
                "workflows": [
                    {
                        "wid": "wf_1",
                        "title": "t",
                        "language": "zh-CN",
                        "images": [],
                        "is_fast_access": False,
                        "browser_settings": {},
                        "chrome_settings": {},
                        "use_in_wechat": False,
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 10,
            }

    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", _FakeClient)
    exit_code = cli_main(["workflow", "list", "--format", "json", "--api-key", "k"])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    workflow = stdout["data"]["workflows"][0]
    assert workflow["wid"] == "wf_1"
    assert "language" not in workflow
    assert "images" not in workflow
    assert "is_fast_access" not in workflow
    assert "browser_settings" not in workflow
    assert "chrome_settings" not in workflow
    assert "use_in_wechat" not in workflow


def test_cli_file_upload_supports_multiple_paths(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path):
    file_a = tmp_path / "a.txt"
    file_b = tmp_path / "b.txt"
    file_a.write_text("aaa", encoding="utf-8")
    file_b.write_text("bbb", encoding="utf-8")

    class _FakeClient:
        def __init__(self, api_key: str, base_url: str | None = None):
            self.api_key = api_key
            self.base_url = base_url

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            return False

        @staticmethod
        def upload_file(path: str):
            name = Path(path).name
            return type(
                "UploadResult",
                (),
                {
                    "oss_path": f"user-upload/api-upload/{name}",
                    "original_filename": name,
                    "file_size": 3,
                    "content_type": "text/plain",
                },
            )()

    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", _FakeClient)

    exit_code = cli_main(["--format", "json", "file", "upload", "--path", str(file_a), "--path", str(file_b), "--api-key", "k"])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert stdout["ok"] is True
    files = stdout["data"]["files"]
    assert len(files) == 2
    assert files[0]["oss_path"].endswith("a.txt")
    assert files[1]["oss_path"].endswith("b.txt")


def test_cli_workflow_run_can_upload_and_bind_files(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path):
    file_a = tmp_path / "a.pdf"
    file_b = tmp_path / "b.pdf"
    file_a.write_text("a", encoding="utf-8")
    file_b.write_text("b", encoding="utf-8")
    captured_run: dict[str, Any] = {}

    class _FakeClient:
        def __init__(self, api_key: str, base_url: str | None = None):
            self.api_key = api_key
            self.base_url = base_url

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            return False

        @staticmethod
        def upload_file(path: str):
            name = Path(path).name
            return type(
                "UploadResult",
                (),
                {
                    "oss_path": f"user-upload/api-upload/{name}",
                    "original_filename": name,
                    "file_size": 1,
                    "content_type": "application/pdf",
                },
            )()

        def run_workflow(self, **kwargs: Any):
            captured_run.update(kwargs)
            return "rid_uploaded"

    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", _FakeClient)

    exit_code = cli_main(
        [
            "--format",
            "json",
            "workflow",
            "run",
            "--wid",
            "wf_upload",
            "--upload-to",
            f"n1:upload_files:{file_a}",
            "--upload-to",
            f"n1:upload_files:{file_b}",
            "--upload-as",
            "list",
            "--api-key",
            "k",
        ]
    )
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert stdout["data"]["rid"] == "rid_uploaded"
    input_fields = captured_run["input_fields"]
    assert len(input_fields) == 1
    assert input_fields[0].node_id == "n1"
    assert input_fields[0].field_name == "upload_files"
    assert input_fields[0].value == ["user-upload/api-upload/a.pdf", "user-upload/api-upload/b.pdf"]


# ---------------------------------------------------------------------------
# New command tests
# ---------------------------------------------------------------------------


def _make_fake_client(**method_overrides: Any) -> type:
    """Build a FakeClient class with configurable method stubs."""

    class _FakeClient:
        def __init__(self, api_key: str, base_url: str | None = None):
            self.api_key = api_key
            self.base_url = base_url

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            return False

    for name, fn in method_overrides.items():
        setattr(_FakeClient, name, fn)
    return _FakeClient


@dataclass
class FakeAgentTask:
    task_id: str = ""
    status: str = "running"
    waiting_question: Any = None


@dataclass
class FakeAgent:
    agent_id: str = ""
    name: str = ""


@dataclass
class FakeCycle:
    cycle_id: str = ""
    status: str = "completed"


@dataclass
class FakeListResponse:
    total: int = 0
    page: int = 1
    page_size: int = 10
    page_count: int = 0


@dataclass
class FakeAgentListResponse(FakeListResponse):
    agents: list = field(default_factory=list)


@dataclass
class FakeTaskListResponse(FakeListResponse):
    tasks: list = field(default_factory=list)


@dataclass
class FakeCycleListResponse:
    cycles: list = field(default_factory=list)
    total: int = 0


@dataclass
class FakeWorkflow:
    wid: str = ""
    title: str = ""


def test_cli_task_agent_task_respond(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    captured: dict[str, Any] = {}

    def respond_to_agent_task(self, task_id: str, tool_call_id: str, response_content: str):
        captured.update(task_id=task_id, tool_call_id=tool_call_id, response_content=response_content)
        return FakeAgentTask(task_id=task_id, status="running")

    FakeClient = _make_fake_client(respond_to_agent_task=respond_to_agent_task)
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", FakeClient)

    exit_code = cli_main([
        "--format", "json", "--api-key", "k",
        "task-agent", "task", "respond",
        "--task-id", "t_1", "--tool-call-id", "tc_1", "--response", "Yes",
    ])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert stdout["command"] == "task-agent task respond"
    assert captured["task_id"] == "t_1"
    assert captured["tool_call_id"] == "tc_1"
    assert captured["response_content"] == "Yes"


def test_cli_task_agent_task_delete(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    deleted_ids: list[str] = []

    def delete_agent_task(self, task_id: str):
        deleted_ids.append(task_id)

    FakeClient = _make_fake_client(delete_agent_task=delete_agent_task)
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", FakeClient)

    exit_code = cli_main([
        "--format", "json", "--api-key", "k",
        "task-agent", "task", "delete", "--task-id", "t_del",
    ])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert stdout["data"]["deleted"] is True
    assert stdout["data"]["task_id"] == "t_del"
    assert deleted_ids == ["t_del"]


def test_cli_task_agent_task_search(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    captured: dict[str, Any] = {}

    def list_agent_tasks(self, **kwargs: Any):
        captured.update(kwargs)
        return FakeTaskListResponse()

    FakeClient = _make_fake_client(list_agent_tasks=list_agent_tasks)
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", FakeClient)

    exit_code = cli_main([
        "--format", "json", "--api-key", "k",
        "task-agent", "task", "search", "--query", "hello",
    ])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert captured["search"] == "hello"


def test_cli_task_agent_cycle_list(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    captured: dict[str, Any] = {}

    def list_agent_cycles(self, task_id: str, cycle_index_offset: int = 0):
        captured.update(task_id=task_id, offset=cycle_index_offset)
        return FakeCycleListResponse()

    FakeClient = _make_fake_client(list_agent_cycles=list_agent_cycles)
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", FakeClient)

    exit_code = cli_main([
        "--format", "json", "--api-key", "k",
        "task-agent", "cycle", "list", "--task-id", "t_1",
    ])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert captured["task_id"] == "t_1"


def test_cli_task_agent_cycle_get(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    captured: dict[str, Any] = {}

    def get_agent_cycle(self, cycle_id: str):
        captured["cycle_id"] = cycle_id
        return FakeCycle(cycle_id=cycle_id)

    FakeClient = _make_fake_client(get_agent_cycle=get_agent_cycle)
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", FakeClient)

    exit_code = cli_main([
        "--format", "json", "--api-key", "k",
        "task-agent", "cycle", "get", "--cycle-id", "c_1",
    ])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert captured["cycle_id"] == "c_1"


def test_cli_task_agent_agent_create(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    captured: dict[str, Any] = {}

    def create_agent(self, **kwargs: Any):
        captured.update(kwargs)
        return FakeAgent(agent_id="a_new", name=kwargs["name"])

    FakeClient = _make_fake_client(create_agent=create_agent)
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", FakeClient)

    exit_code = cli_main([
        "--format", "json", "--api-key", "k",
        "task-agent", "agent", "create", "--name", "TestBot", "--system-prompt", "Be helpful",
    ])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert captured["name"] == "TestBot"
    assert captured["system_prompt"] == "Be helpful"


def test_cli_task_agent_agent_update(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    captured: dict[str, Any] = {}

    def update_agent(self, **kwargs: Any):
        captured.update(kwargs)
        return FakeAgent(agent_id=kwargs["agent_id"], name=kwargs.get("name", "old"))

    FakeClient = _make_fake_client(update_agent=update_agent)
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", FakeClient)

    exit_code = cli_main([
        "--format", "json", "--api-key", "k",
        "task-agent", "agent", "update", "--agent-id", "a_1", "--name", "NewName",
    ])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert captured["agent_id"] == "a_1"
    assert captured["name"] == "NewName"


def test_cli_task_agent_agent_delete(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    deleted_ids: list[str] = []

    def delete_agent(self, agent_id: str):
        deleted_ids.append(agent_id)

    FakeClient = _make_fake_client(delete_agent=delete_agent)
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", FakeClient)

    exit_code = cli_main([
        "--format", "json", "--api-key", "k",
        "task-agent", "agent", "delete", "--agent-id", "a_del",
    ])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert stdout["data"]["deleted"] is True
    assert deleted_ids == ["a_del"]


def test_cli_task_agent_agent_search(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    captured: dict[str, Any] = {}

    def list_agents(self, **kwargs: Any):
        captured.update(kwargs)
        return FakeAgentListResponse()

    FakeClient = _make_fake_client(list_agents=list_agents)
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", FakeClient)

    exit_code = cli_main([
        "--format", "json", "--api-key", "k",
        "task-agent", "agent", "search", "--query", "translator",
    ])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert captured["search"] == "translator"


def test_cli_workflow_create(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    captured: dict[str, Any] = {}

    def create_workflow(self, **kwargs: Any):
        captured.update(kwargs)
        return FakeWorkflow(wid="wf_new", title=kwargs.get("title", "New workflow"))

    FakeClient = _make_fake_client(create_workflow=create_workflow)
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", FakeClient)

    exit_code = cli_main([
        "--format", "json", "--api-key", "k",
        "workflow", "create", "--title", "My Flow", "--source-wid", "wf_src",
    ])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert captured["title"] == "My Flow"
    assert captured["source_workflow_wid"] == "wf_src"


def test_cli_workflow_delete(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    deleted: list[str] = []

    def delete_workflow(self, wid: str):
        deleted.append(wid)
        return {}

    FakeClient = _make_fake_client(delete_workflow=delete_workflow)
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", FakeClient)

    exit_code = cli_main([
        "--format", "json", "--api-key", "k",
        "workflow", "delete", "--wid", "wf_del",
    ])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert deleted == ["wf_del"]


def test_cli_workflow_search(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    captured: dict[str, Any] = {}

    def list_workflows(self, **kwargs: Any):
        captured.update(kwargs)
        return {"workflows": [], "total": 0, "page": 1, "page_size": 10}

    FakeClient = _make_fake_client(list_workflows=list_workflows)
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", FakeClient)

    exit_code = cli_main([
        "--format", "json", "--api-key", "k",
        "workflow", "search", "--query", "translation",
    ])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert captured["search_text"] == "translation"


def test_cli_task_create_with_wait(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    call_count = {"n": 0}

    def create_agent_task(self, **kwargs: Any):
        return FakeAgentTask(task_id="t_wait", status="running")

    def get_agent_task(self, task_id: str):
        call_count["n"] += 1
        status = "completed" if call_count["n"] >= 2 else "running"
        return FakeAgentTask(task_id=task_id, status=status)

    FakeClient = _make_fake_client(create_agent_task=create_agent_task, get_agent_task=get_agent_task)
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", FakeClient)
    monkeypatch.setattr("vectorvein.cli._parsers.time.sleep", lambda _: None)

    exit_code = cli_main([
        "--format", "json", "--api-key", "k",
        "task-agent", "task", "create", "--text", "do it", "--wait", "--timeout", "60",
    ])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert call_count["n"] >= 2


def test_cli_workflow_run_record_list(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    captured: dict[str, Any] = {}

    def list_workflow_run_records(self, **kwargs: Any):
        captured.update(kwargs)
        return {"run_records": [], "total": 0, "page": 1, "page_size": 10}

    FakeClient = _make_fake_client(list_workflow_run_records=list_workflow_run_records)
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", FakeClient)

    exit_code = cli_main([
        "--format", "json", "--api-key", "k",
        "workflow", "run-record", "list", "--wid", "wf_1", "--status", "FINISHED",
    ])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert captured["wid"] == "wf_1"
    assert captured["status"] == ["FINISHED"]


def test_cli_workflow_run_record_get(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    captured: dict[str, Any] = {}

    def get_workflow_run_record(self, rid: str):
        captured["rid"] = rid
        return {"rid": rid, "status": "FINISHED", "data": []}

    FakeClient = _make_fake_client(get_workflow_run_record=get_workflow_run_record)
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", FakeClient)

    exit_code = cli_main([
        "--format", "json", "--api-key", "k",
        "workflow", "run-record", "get", "--rid", "rid_123",
    ])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert captured["rid"] == "rid_123"
    assert stdout["data"]["rid"] == "rid_123"


def test_cli_workflow_run_record_stop(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    captured: dict[str, Any] = {}

    def stop_workflow_run_record(self, rid: str):
        captured["rid"] = rid
        return {"rid": rid, "stopped": True}

    FakeClient = _make_fake_client(stop_workflow_run_record=stop_workflow_run_record)
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", FakeClient)

    exit_code = cli_main([
        "--format", "json", "--api-key", "k",
        "workflow", "run-record", "stop", "--rid", "rid_running",
    ])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert captured["rid"] == "rid_running"


def test_cli_workflow_describe(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    @dataclass
    class FakeWorkflowFull:
        wid: str = "wf_desc"
        title: str = "Translation Flow"
        brief: str = "Translate text"
        data: dict = field(default_factory=lambda: {
            "nodes": [
                {
                    "id": "node_1",
                    "data": {
                        "template": {
                            "input_text": {
                                "display_name": "Input Text",
                                "field_type": "text",
                                "required": True,
                                "show": True,
                                "is_output": False,
                                "value": "",
                            },
                            "target_lang": {
                                "display_name": "Target Language",
                                "field_type": "select",
                                "required": True,
                                "show": True,
                                "is_output": False,
                                "value": "en",
                                "options": [{"label": "English", "value": "en"}, {"label": "Chinese", "value": "zh"}],
                            },
                            "output": {
                                "display_name": "Output",
                                "field_type": "text",
                                "is_output": True,
                                "show": True,
                                "value": "",
                            },
                        }
                    },
                }
            ],
            "edges": [],
        })

    def get_workflow(self, wid: str):
        return FakeWorkflowFull(wid=wid)

    FakeClient = _make_fake_client(get_workflow=get_workflow)
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", FakeClient)

    exit_code = cli_main([
        "--format", "json", "--api-key", "k",
        "workflow", "describe", "--wid", "wf_desc",
    ])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    data = stdout["data"]
    assert data["wid"] == "wf_desc"
    assert data["title"] == "Translation Flow"
    assert len(data["input_fields"]) == 2
    names = {f["field_name"] for f in data["input_fields"]}
    assert names == {"input_text", "target_lang"}
    lang_field = next(f for f in data["input_fields"] if f["field_name"] == "target_lang")
    assert lang_field["default"] == "en"
    assert "options" in lang_field


def test_cli_task_continue_with_wait(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    poll_count = {"n": 0}

    def continue_agent_task(self, **kwargs: Any):
        return FakeAgentTask(task_id=kwargs["task_id"], status="running")

    def get_agent_task(self, task_id: str):
        poll_count["n"] += 1
        status = "completed" if poll_count["n"] >= 2 else "running"
        return FakeAgentTask(task_id=task_id, status=status)

    FakeClient = _make_fake_client(continue_agent_task=continue_agent_task, get_agent_task=get_agent_task)
    monkeypatch.setattr("vectorvein.cli.main.VectorVeinClient", FakeClient)
    monkeypatch.setattr("vectorvein.cli._parsers.time.sleep", lambda _: None)

    exit_code = cli_main([
        "--format", "json", "--api-key", "k",
        "task-agent", "task", "continue",
        "--task-id", "t_1", "--message", "go on", "--wait", "--timeout", "60",
    ])
    stdout, stderr = _read_json_output(capsys)

    assert exit_code == 0
    assert stderr == {}
    assert poll_count["n"] >= 2
