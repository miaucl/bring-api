"""Tests for get_activity method."""

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
async def test_get_activity(
    bring: Bring,
    snapshot: SnapshotAssertion,
) -> None:
    """Test get_activity."""
    await bring.login()
    activity = await bring.get_activity(UUID)

    assert activity == snapshot


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
        f"https://api.getbring.com/rest/v2/bringlists/{UUID}/activity",
        exception=exception,
    )

    with pytest.raises(BringRequestException):
        await bring.get_activity(UUID)


async def test_auth_exception(
    mocked: aioresponses,
    bring: Bring,
) -> None:
    """Test request exceptions."""
    await bring.login()
    mocked.clear()
    mocked.get(
        f"https://api.getbring.com/rest/v2/bringlists/{UUID}/activity",
        status=HTTPStatus.UNAUTHORIZED,
        body=load_fixture("error_response.json"),
    )

    with pytest.raises(BringAuthException):
        await bring.get_activity(UUID)


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
    mocked.get(
        f"https://api.getbring.com/rest/v2/bringlists/{UUID}/activity",
        status=status,
        body="not json",
        content_type="application/json",
    )

    with pytest.raises(exception):
        await bring.get_activity(UUID)
