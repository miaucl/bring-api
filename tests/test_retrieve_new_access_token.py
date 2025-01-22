"""Test for retrieve_new_access_token method."""

import asyncio
from http import HTTPStatus
from unittest.mock import patch

import aiohttp
from aioresponses import aioresponses
import pytest
from syrupy.assertion import SnapshotAssertion

from bring_api import (
    Bring,
    BringAuthException,
    BringParseException,
    BringRequestException,
)

from .conftest import load_fixture


@pytest.mark.usefixtures("mocked")
async def test_retrieve_new_access_token(
    bring: Bring,
    snapshot: SnapshotAssertion,
) -> None:
    """Test retrieve_new_access_token."""
    await bring.login()

    with patch("time.time", return_value=0):
        data = await bring.retrieve_new_access_token()

        assert data == snapshot
        assert bring.headers["Authorization"] == "Bearer {access_token}"
        assert bring._expires_at == 604799


@pytest.mark.parametrize(
    "exception",
    [
        asyncio.TimeoutError,
        aiohttp.ClientError,
    ],
)
async def test_request_exception(
    mocked: aioresponses,
    bring: Bring,
    exception: type[Exception],
) -> None:
    """Test request exceptions."""
    await bring.login()
    mocked.clear()
    mocked.post(
        "https://api.getbring.com/rest/v2/bringauth/token",
        exception=exception,
    )

    with pytest.raises(BringRequestException):
        await bring.retrieve_new_access_token()


async def test_auth_exception(
    mocked: aioresponses,
    bring: Bring,
) -> None:
    """Test request exceptions."""
    await bring.login()
    mocked.clear()
    mocked.post(
        "https://api.getbring.com/rest/v2/bringauth/token",
        status=HTTPStatus.UNAUTHORIZED,
        body=load_fixture("error_response.json"),
    )

    with pytest.raises(BringAuthException):
        await bring.retrieve_new_access_token()


@pytest.mark.parametrize(
    ("status", "exception"),
    [
        (HTTPStatus.OK, BringParseException),
        (HTTPStatus.UNAUTHORIZED, BringAuthException),
    ],
)
async def test_parse_exception(
    mocked: aioresponses,
    bring: Bring,
    status: HTTPStatus,
    exception: type[Exception],
) -> None:
    """Test request exceptions."""
    await bring.login()
    mocked.clear()
    mocked.post(
        "https://api.getbring.com/rest/v2/bringauth/token",
        status=status,
        body="not json",
        content_type="application/json",
    )

    with pytest.raises(exception):
        await bring.retrieve_new_access_token()
