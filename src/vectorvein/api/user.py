"""User API functionality."""

from typing import Any

from .exceptions import VectorVeinAPIError
from .models import APIUserIdentity


def _parse_user_identity(response_data: Any) -> APIUserIdentity:
    if not isinstance(response_data, dict):
        raise VectorVeinAPIError("Invalid API response for user identity")

    return APIUserIdentity(
        user_id=str(response_data.get("user_id", "")),
        username=str(response_data.get("username", "")),
    )


class UserSyncMixin:
    """Synchronous user API methods."""

    def get_user_info(self) -> dict[str, Any]:
        """Get current user profile information."""
        response = self._request("GET", "user-info/get")
        data = response.get("data")
        if not isinstance(data, dict):
            raise VectorVeinAPIError("Invalid API response for user info", status_code=response.get("status"))
        return data

    def validate_api_key(self) -> APIUserIdentity:
        """Validate API key and return identity info."""
        response = self._request("GET", "user/validate-api-key")
        return _parse_user_identity(response.get("data"))


class UserAsyncMixin:
    """Asynchronous user API methods."""

    async def get_user_info(self) -> dict[str, Any]:
        """Get current user profile information."""
        response = await self._request("GET", "user-info/get")
        data = response.get("data")
        if not isinstance(data, dict):
            raise VectorVeinAPIError("Invalid API response for user info", status_code=response.get("status"))
        return data

    async def validate_api_key(self) -> APIUserIdentity:
        """Validate API key and return identity info."""
        response = await self._request("GET", "user/validate-api-key")
        return _parse_user_identity(response.get("data"))
