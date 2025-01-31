"""Test headers serializing functions."""

from bring_api.const import DEFAULT_HEADERS
from bring_api.helpers import headers_deserialize, headers_serialize


async def test_headers_deserialize(headers: str) -> None:
    """Test deserializing of headers."""

    headers_dict = headers_deserialize(headers)

    assert isinstance(headers_dict, dict), "Headers are not a dict"
    assert len(headers_dict.keys()) > 0, "Cookies list is empty"

    assert headers_dict["X-BRING-API-KEY"], "Token is None"
    assert len(headers_dict["X-BRING-API-KEY"]) > 0, "Token is empty"


async def test_cookies_serialize() -> None:
    """Test serializing of headers."""

    headers = headers_serialize(DEFAULT_HEADERS.copy())

    assert len(headers) > 0, "Headers are not correctly serialized"
    assert "X-BRING-API-KEY" in headers, "Headers do not contain X-BRING-API-KEY"
