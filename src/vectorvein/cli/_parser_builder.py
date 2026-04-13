"""Build the top-level CLI argument parser and register domain builders."""

from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, version as package_version

from vectorvein.cli._builders.api import register_api_parser
from vectorvein.cli._builders.auth import register_auth_parsers
from vectorvein.cli._builders.common import RichHelpFormatter
from vectorvein.cli._builders.file import register_file_parser
from vectorvein.cli._builders.task_agent import register_task_agent_parser
from vectorvein.cli._builders.workflow import register_workflow_parser
from vectorvein.cli._builders.workspace import register_workspace_parser
from vectorvein.cli._output import CLIArgumentParser
from vectorvein.cli._parsers import ENV_API_KEY, ENV_BASE_URL


def _current_version() -> str:
    try:
        return package_version("vectorvein-sdk")
    except PackageNotFoundError:
        return "dev"


def build_parser() -> argparse.ArgumentParser:
    parser = CLIArgumentParser(
        prog="vectorvein",
        description=(
            "VectorVein command line interface.\n"
            "Text output is human-friendly by default; use --format json for machine-readable responses.\n"
            f"API key resolution order: --api-key > {ENV_API_KEY}.\n"
            f"Base URL resolution order: --base-url > {ENV_BASE_URL}."
        ),
        epilog=(
            "Examples:\n"
            "  vectorvein auth whoami\n"
            "  vectorvein workflow describe --wid wf_xxx\n"
            "  vectorvein workflow run --wid wf_xxx --input-fields @inputs.json --wait\n"
            "  vectorvein task-agent agent create --name 'Research Assistant'\n"
            "  vectorvein task-agent task create --agent-id agent_xxx --text 'Summarize this report' --wait\n"
            "  vectorvein task-agent skill install --skill-id skill_xxx --permission-level auto\n"
            "  vectorvein agent-workspace read --workspace-id ws_xxx --file-path notes.txt --start-line 1 --end-line 20\n"
            '  vectorvein api request --method POST --endpoint workflow/list --body \'{"page":1,"page_size":5}\'\n\n'
            "JSON inputs support @file syntax, for example --input-fields @payload.json.\n\n"
            "Exit codes:\n"
            "  0 success\n"
            "  1 unexpected error\n"
            "  2 invalid usage or arguments\n"
            "  3 authentication/API key error\n"
            "  4 API business error\n"
            "  5 network/request error"
        ),
        formatter_class=RichHelpFormatter,
    )
    parser.add_argument("--api-key", help=f"VectorVein API key. Overrides {ENV_API_KEY}.")
    parser.add_argument("--base-url", help=f"Open API base URL. Overrides {ENV_BASE_URL}.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format (default: text).")
    parser.add_argument("--compact", action="store_true", help="Output compact one-line JSON.")
    parser.add_argument("--debug", action="store_true", help="Include traceback details in error output.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {_current_version()}")

    top_level = parser.add_subparsers(dest="module")
    top_level.required = True

    register_auth_parsers(top_level)
    register_workflow_parser(top_level)
    register_file_parser(top_level)
    register_task_agent_parser(top_level)
    register_workspace_parser(top_level)
    register_api_parser(top_level)

    return parser
