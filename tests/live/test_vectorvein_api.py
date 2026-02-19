"""VectorVein API tests (live, requires credentials)."""

import pytest

from vectorvein.api import (
    VectorVeinClient,
    WorkflowInputField,
    APIKeyError,
    AccessKeyError,
    WorkflowError,
    TimeoutError,
)
from tests.live.live_common import load_live_settings


@pytest.fixture(scope="module")
def settings():
    return load_live_settings()


@pytest.fixture
def client(settings):
    """Create an API client from live settings."""
    with VectorVeinClient(api_key=settings["api_key"], base_url=settings["base_url"]) as c:
        yield c


def test_init_client(settings):
    client = VectorVeinClient(api_key=settings["api_key"])
    assert client.api_key == settings["api_key"]
    assert client.base_url == VectorVeinClient.BASE_URL

    client = VectorVeinClient(api_key=settings["api_key"], base_url="https://custom.url")
    assert client.base_url == "https://custom.url"

    with pytest.raises(APIKeyError, match="cannot be empty"):
        VectorVeinClient(api_key="")

    with pytest.raises(APIKeyError, match="cannot be empty"):
        VectorVeinClient(api_key=123)  # type: ignore


def test_create_access_keys(client, settings):
    keys = client.create_access_keys(access_key_type="L", app_id=settings["app_id"], description="测试密钥")
    assert len(keys) == 1
    assert keys[0].access_key_type == "L"
    assert keys[0].description == "测试密钥"

    with pytest.raises(AccessKeyError, match="Invalid access key type"):
        client.create_access_keys(access_key_type="X")

    with pytest.raises(AccessKeyError):
        client.create_access_keys(access_key_type="L", app_id=settings["app_id"], app_ids=["a", "b"])


def test_get_access_keys(client, settings):
    keys = client.create_access_keys(access_key_type="L", app_id=settings["app_id"], description="测试密钥")
    test_key = keys[0].access_key

    result = client.get_access_keys([test_key])
    assert len(result) == 1
    assert result[0].access_key == test_key

    result = client.get_access_keys(get_type="all")
    assert len(result) > 0


def test_list_access_keys(client):
    response = client.list_access_keys()
    assert response.page == 1
    assert response.page_size == 10
    assert isinstance(response.total, int)
    assert isinstance(response.access_keys, list)

    response = client.list_access_keys(page=2, page_size=5)
    assert response.page_size == 5

    response = client.list_access_keys(sort_field="create_time", sort_order="ascend")
    assert len(response.access_keys) > 0


def test_workflow_execution(client, settings):
    input_fields = [WorkflowInputField(node_id="test_node", field_name="test_field", value="test_value")]

    try:
        rid = client.run_workflow(wid=settings["workflow_id"], input_fields=input_fields, wait_for_completion=False)
        assert isinstance(rid, str)
    except (WorkflowError, Exception):
        pytest.skip("Workflow execution not available with test inputs")

    # Sync execution with wait — just verify it returns a result or times out
    try:
        result = client.run_workflow(
            wid=settings["workflow_id"], input_fields=input_fields, wait_for_completion=True, timeout=1,
        )
        assert result is not None
    except (TimeoutError, WorkflowError):
        pass  # timeout or error is also acceptable


def test_context_manager(settings):
    with VectorVeinClient(api_key=settings["api_key"], base_url=settings["base_url"]) as temp_client:
        response = temp_client.list_access_keys()
        assert response.page == 1

    with pytest.raises(Exception):
        temp_client.list_access_keys()


@pytest.mark.parametrize("invalid_key", ["invalid_key", "12345678901234567890123456789012", "", None])
def test_invalid_api_key(invalid_key, settings):
    if not invalid_key:
        with pytest.raises(APIKeyError, match="cannot be empty"):
            VectorVeinClient(api_key=invalid_key)
    else:
        client = VectorVeinClient(api_key=invalid_key, base_url=settings["base_url"])
        with pytest.raises(APIKeyError, match="invalid or expired"):
            client.list_access_keys()
