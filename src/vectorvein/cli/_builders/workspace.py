"""Agent workspace parser builder."""

from __future__ import annotations

import argparse

from vectorvein.cli._builders.common import add_paging_arguments, rich_parser_kwargs
from vectorvein.cli._commands.workspace import (
    _cmd_workspace_delete,
    _cmd_workspace_download,
    _cmd_workspace_files,
    _cmd_workspace_get,
    _cmd_workspace_list,
    _cmd_workspace_read,
    _cmd_workspace_sync,
    _cmd_workspace_write,
    _cmd_workspace_zip,
)


def register_workspace_parser(top_level: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    workspace_parser = top_level.add_parser(
        "agent-workspace",
        help="Agent workspace commands.",
        **rich_parser_kwargs(
            "Inspect, read, and manage files stored in agent task workspaces.",
            examples=[
                "vectorvein agent-workspace list",
                "vectorvein agent-workspace files --workspace-id ws_xxx",
                "vectorvein agent-workspace read --workspace-id ws_xxx --file-path notes.txt --start-line 1 --end-line 20",
            ],
        ),
    )
    workspace_sub = workspace_parser.add_subparsers(dest="workspace_command")
    workspace_sub.required = True

    workspace_list = workspace_sub.add_parser(
        "list",
        help="List agent workspaces.",
        **rich_parser_kwargs("List workspaces that belong to the current account.", examples=["vectorvein agent-workspace list"]),
    )
    add_paging_arguments(workspace_list)
    workspace_list.set_defaults(handler=_cmd_workspace_list, command="agent-workspace list")

    workspace_get = workspace_sub.add_parser(
        "get",
        help="Get one workspace by ID.",
        **rich_parser_kwargs("Fetch a workspace summary by ID.", examples=["vectorvein agent-workspace get --workspace-id ws_xxx"]),
    )
    workspace_get.add_argument("--workspace-id", required=True, help="Workspace ID.")
    workspace_get.set_defaults(handler=_cmd_workspace_get, command="agent-workspace get")

    workspace_files = workspace_sub.add_parser(
        "files",
        help="List files in a workspace.",
        **rich_parser_kwargs(
            "List workspace files, optionally filtered by prefix or rendered as a tree.", examples=["vectorvein agent-workspace files --workspace-id ws_xxx --tree-view"]
        ),
    )
    workspace_files.add_argument("--workspace-id", required=True, help="Workspace ID.")
    workspace_files.add_argument("--prefix", help="Path prefix filter.")
    workspace_files.add_argument("--tree-view", action="store_true", help="Return files in tree-view style.")
    workspace_files.set_defaults(handler=_cmd_workspace_files, command="agent-workspace files")

    workspace_read = workspace_sub.add_parser(
        "read",
        help="Read a workspace file.",
        **rich_parser_kwargs(
            "Read a UTF-8 workspace file, optionally limiting the output to a line range.",
            examples=["vectorvein agent-workspace read --workspace-id ws_xxx --file-path notes.txt --start-line 1 --end-line 20"],
        ),
    )
    workspace_read.add_argument("--workspace-id", required=True, help="Workspace ID.")
    workspace_read.add_argument("--file-path", required=True, help="File path in workspace.")
    workspace_read.add_argument("--start-line", type=int, help="Start line (1-based).")
    workspace_read.add_argument("--end-line", type=int, help="End line (1-based, inclusive).")
    workspace_read.set_defaults(handler=_cmd_workspace_read, command="agent-workspace read")

    workspace_write = workspace_sub.add_parser(
        "write",
        help="Write a workspace file.",
        **rich_parser_kwargs(
            "Write UTF-8 content into a workspace file. Use either inline --content or a local --content-file.",
            examples=[
                "vectorvein agent-workspace write --workspace-id ws_xxx --file-path notes.txt --content 'hello'",
                "vectorvein agent-workspace write --workspace-id ws_xxx --file-path notes.txt --content-file ./notes.txt",
            ],
        ),
    )
    workspace_write.add_argument("--workspace-id", required=True, help="Workspace ID.")
    workspace_write.add_argument("--file-path", required=True, help="File path in workspace.")
    workspace_write.add_argument("--content", help="Inline UTF-8 text content or @file.")
    workspace_write.add_argument("--content-file", help="Read file content from local UTF-8 file.")
    workspace_write.set_defaults(handler=_cmd_workspace_write, command="agent-workspace write")

    workspace_delete = workspace_sub.add_parser(
        "delete",
        help="Delete a workspace file.",
        **rich_parser_kwargs("Delete a file from a workspace.", examples=["vectorvein agent-workspace delete --workspace-id ws_xxx --file-path notes.txt"]),
    )
    workspace_delete.add_argument("--workspace-id", required=True, help="Workspace ID.")
    workspace_delete.add_argument("--file-path", required=True, help="File path in workspace.")
    workspace_delete.set_defaults(handler=_cmd_workspace_delete, command="agent-workspace delete")

    workspace_download = workspace_sub.add_parser(
        "download",
        help="Get temporary download URL for a workspace file.",
        **rich_parser_kwargs("Get a temporary download URL for a workspace file.", examples=["vectorvein agent-workspace download --workspace-id ws_xxx --file-path archive.zip"]),
    )
    workspace_download.add_argument("--workspace-id", required=True, help="Workspace ID.")
    workspace_download.add_argument("--file-path", required=True, help="File path in workspace.")
    workspace_download.set_defaults(handler=_cmd_workspace_download, command="agent-workspace download")

    workspace_zip = workspace_sub.add_parser(
        "zip",
        help="Zip entire workspace and return download metadata.",
        **rich_parser_kwargs("Bundle a workspace into a zip archive and return download metadata.", examples=["vectorvein agent-workspace zip --workspace-id ws_xxx"]),
    )
    workspace_zip.add_argument("--workspace-id", required=True, help="Workspace ID.")
    workspace_zip.set_defaults(handler=_cmd_workspace_zip, command="agent-workspace zip")

    workspace_sync = workspace_sub.add_parser(
        "sync",
        help="Trigger container-to-OSS sync for workspace.",
        **rich_parser_kwargs("Trigger a workspace sync from the runtime container back to OSS storage.", examples=["vectorvein agent-workspace sync --workspace-id ws_xxx"]),
    )
    workspace_sync.add_argument("--workspace-id", required=True, help="Workspace ID.")
    workspace_sync.set_defaults(handler=_cmd_workspace_sync, command="agent-workspace sync")
