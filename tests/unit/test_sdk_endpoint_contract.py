"""All SDK endpoints must exist in the reviewed backend route snapshot."""

import ast
import inspect
import json
from pathlib import Path

from vectorvein.api import access_key, agent_workspace, file_upload, task_agent, user, workflow


_API_DIRECTORY = Path(__file__).parents[2] / "src/vectorvein/api"


def test_all_sdk_endpoints_exist_in_backend_snapshot():
    fixture = json.loads((Path(__file__).parents[1] / "fixtures/open_api_routes.json").read_text())
    endpoints = set()
    for path in _API_DIRECTORY.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in {"_request", "_workflow_post"}:
                continue
            position = 1 if node.func.attr == "_request" else 0
            if len(node.args) > position and isinstance(node.args[position], ast.Constant):
                endpoints.add(node.args[position].value)
    assert endpoints
    assert endpoints <= set(fixture["routes"]), endpoints - set(fixture["routes"])


def test_every_api_mixin_has_matching_sync_async_methods_and_signatures():
    for module in (access_key, agent_workspace, file_upload, task_agent, user, workflow):
        for name, sync_class in vars(module).items():
            if not name.endswith("SyncMixin"):
                continue
            async_class = getattr(module, name.replace("SyncMixin", "AsyncMixin"))
            sync_methods = {name: method for name, method in vars(sync_class).items() if inspect.isfunction(method)}
            async_methods = {name: method for name, method in vars(async_class).items() if inspect.isfunction(method)}
            assert sync_methods.keys() == async_methods.keys()
            for name, method in sync_methods.items():
                assert inspect.signature(method) == inspect.signature(async_methods[name]), (module.__name__, name)
