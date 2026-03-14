"""File upload command handler."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from vectorvein.api import VectorVeinClient

from vectorvein.cli._output import CLIUsageError


def _cmd_file_upload(args: argparse.Namespace, client: VectorVeinClient) -> dict[str, Any]:
    uploaded_files: list[dict[str, Any]] = []
    for index, path_text in enumerate(args.path or [], start=1):
        local_path = Path(path_text)
        if not local_path.exists():
            raise CLIUsageError(f"--path[{index}] does not exist: {local_path}")
        if not local_path.is_file():
            raise CLIUsageError(f"--path[{index}] must be a file path: {local_path}")

        upload_result = client.upload_file(str(local_path))
        uploaded_files.append(
            {
                "local_path": str(local_path),
                "oss_path": upload_result.oss_path,
                "original_filename": upload_result.original_filename,
                "file_size": upload_result.file_size,
                "content_type": upload_result.content_type,
            }
        )
    return {"files": uploaded_files}
