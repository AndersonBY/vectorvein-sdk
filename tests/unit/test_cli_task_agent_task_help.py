import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from vectorvein.cli._parser_builder import build_parser
from vectorvein.cli.main import main as cli_main


def test_task_create_help_mentions_tokens_schema(capsys: pytest.CaptureFixture[str]):
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["task-agent", "task", "create", "-h"])

    out = capsys.readouterr().out
    assert "compress_memory_after_tokens" in out
    assert "compress_memory_after_characters" not in out
    assert "JSON object or @file" in out
    assert "--agent-definition" in out
    assert "--agent-settings" in out
    assert "Examples:" in out


def test_task_create_rejects_legacy_character_schema_with_fix_hint(capsys: pytest.CaptureFixture[str]):
    exit_code = cli_main(
        [
            "--api-key",
            "test_key",
            "task-agent",
            "task",
            "create",
            "--text",
            "Analyze the report.",
            "--agent-definition",
            '{"model_name":"gpt-4o","backend_type":"openai","compress_memory_after_characters":64000}',
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "compress_memory_after_characters" in captured.err
    assert "compress_memory_after_tokens" in captured.err
    assert "Rename compress_memory_after_characters -> compress_memory_after_tokens." in captured.err
