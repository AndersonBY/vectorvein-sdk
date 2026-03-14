"""Auth and user command handlers."""

from __future__ import annotations

import argparse
from typing import Any

from vectorvein.api import VectorVeinClient


def _cmd_auth_whoami(args: argparse.Namespace, client: VectorVeinClient) -> dict[str, Any]:
    info = client.get_user_info()
    return {
        "uid": str(info.get("uid", "")),
        "username": str(info.get("username", "")),
        "email": str(info.get("email", "")),
        "credits": int(info.get("credits", 0) or 0),
        "date_joined": str(info.get("date_joined", "")),
    }


def _cmd_user_info(args: argparse.Namespace, client: VectorVeinClient) -> dict[str, Any]:
    return client.get_user_info()


def _cmd_user_validate_api_key(args: argparse.Namespace, client: VectorVeinClient) -> dict[str, str]:
    identity = client.validate_api_key()
    return {"user_id": identity.user_id, "username": identity.username}
