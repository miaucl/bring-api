"""Tests for get_user_account method."""

import asyncio
from http import HTTPStatus

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

from .conftest import UUID, load_fixture


@pytest.mark.usefixtures("mocked")
async def test_get_user_account(
    bring: Bring,
    snapshot: SnapshotAssertion,
) -> None:
    """Test for get_user_account."""
    await bring.login()
    data = await bring.get_user_account()

    assert data == snapshot


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
    mocked.get(
        f"https://api.getbring.com/rest/v2/bringusers/{UUID}",
        exception=exception,
    )

    with pytest.raises(BringRequestException):
        await bring.get_user_account()


async def test_unauthorized(
    mocked: aioresponses,
    bring: Bring,
) -> None:
    """Test unauthorized exception."""
    await bring.login()
    mocked.clear()
    mocked.get(
        f"https://api.getbring.com/rest/v2/bringusers/{UUID}",
        status=HTTPStatus.UNAUTHORIZED,
        body=load_fixture("error_response.json"),
    )

    with pytest.raises(BringAuthException):
        await bring.get_user_account()


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
    """Test parse exceptions."""
    await bring.login()
    mocked.clear()
    mocked.get(
        f"https://api.getbring.com/rest/v2/bringusers/{UUID}",
        status=status,
        body="not json",
        content_type="application/json",
    )

    with pytest.raises(exception):
        await bring.get_user_account()
