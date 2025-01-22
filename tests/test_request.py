"""Tests for request method."""

import asyncio
from http import HTTPStatus

import aiohttp
from aioresponses import aioresponses
import pytest
from yarl import URL

from bring_api import Bring, BringAuthException, BringRequestException

from .conftest import DEFAULT_HEADERS, load_fixture


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
    mocked.get(
        URL("https://api.getbring.com"),
        exception=exception,
    )

    with pytest.raises(BringRequestException):
        await bring._request("get", URL("https://api.getbring.com"))


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
        repeat=True,
    )
    mocked.get(
        URL("https://api.getbring.com"),
        status=HTTPStatus.UNAUTHORIZED,
        body=load_fixture("error_response.json"),
        repeat=True,
    )

    with pytest.raises(BringAuthException):
        await bring._request("get", URL("https://api.getbring.com"))


async def test_auth_expired(
    mocked: aioresponses,
    bring: Bring,
) -> None:
    """Test refresh token before api request."""
    await bring.login()
    mocked.clear()
    bring._expires_at = 0

    mocked.post(
        "https://api.getbring.com/rest/v2/bringauth/token",
        status=HTTPStatus.OK,
        body=load_fixture("token_response.json"),
        repeat=True,
    )
    mocked.get(
        URL("https://api.getbring.com/test"),
        status=HTTPStatus.OK,
        repeat=True,
    )

    await bring._request("GET", URL("https://api.getbring.com/test"))

    mocked.assert_called_with(
        "https://api.getbring.com/test",
        method="get",
        headers=DEFAULT_HEADERS,
    )
