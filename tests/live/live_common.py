from __future__ import annotations

TRUTHY = {"1", "true", "yes", "on"}


def _is_placeholder(value: str) -> bool:
    return value.strip().startswith("YOUR_")


def load_live_settings() -> dict:
    """Load and validate live test credentials from sample_settings.

    Returns a dict with all credential keys.
    Raises RuntimeError if no usable credentials are found.
    """
    from tests.sample_settings import (
        VECTORVEIN_API_KEY,
        VECTORVEIN_BASE_URL,
        VECTORVEIN_APP_ID,
        VECTORVEIN_WORKFLOW_ID,
        VECTORVEIN_VPP_API_KEY,
        VECTORVEIN_VAPP_ID,
    )

    settings = {
        "api_key": VECTORVEIN_API_KEY,
        "base_url": VECTORVEIN_BASE_URL,
        "app_id": VECTORVEIN_APP_ID,
        "workflow_id": VECTORVEIN_WORKFLOW_ID,
        "vpp_api_key": VECTORVEIN_VPP_API_KEY,
        "vapp_id": VECTORVEIN_VAPP_ID,
    }

    if not VECTORVEIN_API_KEY or _is_placeholder(VECTORVEIN_API_KEY):
        raise RuntimeError(
            "Live settings have no usable API credentials. "
            "Create tests/dev_settings.py from tests/dev_settings.example.py."
        )

    return settings
