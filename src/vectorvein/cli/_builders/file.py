"""File parser builders."""

from __future__ import annotations

import argparse

from vectorvein.cli._builders.common import rich_parser_kwargs
from vectorvein.cli._commands.file import _cmd_file_upload


def register_file_parser(top_level: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    file_parser = top_level.add_parser(
        "file",
        help="File upload commands.",
        **rich_parser_kwargs(
            "Upload local files to VectorVein and return reusable OSS paths.",
            examples=[
                "vectorvein file upload --path ./report.pdf",
                "vectorvein file upload --path ./report.pdf --path ./appendix.pdf",
            ],
        ),
    )
    file_sub = file_parser.add_subparsers(dest="file_command")
    file_sub.required = True

    file_upload = file_sub.add_parser(
        "upload",
        help="Upload local file(s) and return OSS path(s).",
        **rich_parser_kwargs(
            "Upload one or more local files and receive OSS metadata that can be reused in workflow and task-agent commands.",
            examples=[
                "vectorvein file upload --path ./report.pdf",
                "vectorvein file upload --path ./report.pdf --path ./appendix.pdf",
            ],
        ),
    )
    file_upload.add_argument("--path", action="append", required=True, help="Local file path to upload. Repeat for multiple files.")
    file_upload.set_defaults(handler=_cmd_file_upload, command="file upload")
