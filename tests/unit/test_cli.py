import json
import sys
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
