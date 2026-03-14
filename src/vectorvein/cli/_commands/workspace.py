"""Agent-workspace command handlers."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from vectorvein.api import VectorVeinClient

from vectorvein.cli._output import CLIUsageError


def _cmd_workspace_list(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_agent_workspaces(page=args.page, page_size=args.page_size)


def _cmd_workspace_get(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.get_agent_workspace(workspace_id=args.workspace_id)


def _cmd_workspace_files(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.list_workspace_files(
        workspace_id=args.workspace_id,
        prefix=args.prefix,
        tree_view=args.tree_view,
    )


def _cmd_workspace_read(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.read_workspace_file(
        workspace_id=args.workspace_id,
        file_path=args.file_path,
        start_line=args.start_line,
        end_line=args.end_line,
    )


def _cmd_workspace_write(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    use_inline = args.content is not None
    use_file = args.content_file is not None
    if use_inline == use_file:
        raise CLIUsageError("workspace write requires exactly one of --content or --content-file.")

    if use_file:
        path = Path(args.content_file)
        if not path.exists():
            raise CLIUsageError(f"--content-file does not exist: {path}")
        if not path.is_file():
            raise CLIUsageError(f"--content-file must be a file path: {path}")
        content = path.read_text(encoding="utf-8")
    else:
        content = str(args.content)

    return client.write_workspace_file(
        workspace_id=args.workspace_id,
        file_path=args.file_path,
        content=content,
    )


def _cmd_workspace_delete(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.delete_workspace_file(workspace_id=args.workspace_id, file_path=args.file_path)


def _cmd_workspace_download(args: argparse.Namespace, client: VectorVeinClient) -> dict[str, str]:
    file_url = client.download_workspace_file(workspace_id=args.workspace_id, file_path=args.file_path)
    return {"file_url": file_url}


def _cmd_workspace_zip(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.zip_workspace_files(workspace_id=args.workspace_id)


def _cmd_workspace_sync(args: argparse.Namespace, client: VectorVeinClient) -> Any:
    return client.sync_workspace_container_to_oss(workspace_id=args.workspace_id)
