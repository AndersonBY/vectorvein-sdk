try:
    from tests.dev_settings import (
        VECTORVEIN_API_KEY,
        VECTORVEIN_BASE_URL,
        VECTORVEIN_APP_ID,
        VECTORVEIN_WORKFLOW_ID,
        VECTORVEIN_VPP_API_KEY,
        VECTORVEIN_VAPP_ID,
    )
except ImportError:
    VECTORVEIN_API_KEY = ""
    VECTORVEIN_BASE_URL = "https://vectorvein.com/api/v1/open-api"
    VECTORVEIN_APP_ID = ""
    VECTORVEIN_WORKFLOW_ID = ""
    VECTORVEIN_VPP_API_KEY = ""
    VECTORVEIN_VAPP_ID = ""
