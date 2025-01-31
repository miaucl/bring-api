"""Tests for login method."""

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
async def test_login(
    bring: Bring,
    snapshot: SnapshotAssertion,
) -> None:
    """Test login with valid user."""

    data = await bring.login()
    assert data == snapshot
    assert bring.headers["Authorization"] == "Bearer ACCESS_TOKEN"
    assert bring.headers["X-BRING-COUNTRY"] == "DE"
    assert bring.uuid == UUID
    assert bring.public_uuid == UUID
    assert bring.user_locale == "de-DE"


async def test_mail_invalid(
    mocked: aioresponses,
    bring: Bring,
) -> None:
    """Test login with invalid e-mail."""
    mocked.clear()
    mocked.post(
        "https://api.getbring.com/rest/v2/bringauth",
        status=400,
    )
    expected = "Login failed due to bad request, please check your email."
    with pytest.raises(BringAuthException, match=expected):
        await bring.login()


async def test_unauthorized(
    mocked: aioresponses,
    bring: Bring,
) -> None:
    """Test login with unauthorized user."""
    mocked.clear()
    mocked.post(
        "https://api.getbring.com/rest/v2/bringauth",
        status=HTTPStatus.UNAUTHORIZED,
        body=load_fixture("error_response.json"),
    )
    expected = "Login failed due to authorization failure, please check your email and password."
    with pytest.raises(BringAuthException, match=expected):
        await bring.login()


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
    mocked.clear()
    mocked.post(
        "https://api.getbring.com/rest/v2/bringauth",
        status=status,
        body="not json",
        content_type="application/json",
    )

    with pytest.raises(exception):
        await bring.login()


@pytest.mark.parametrize(
    "exception",
    [
        asyncio.TimeoutError,
        aiohttp.ClientError,
    ],
)
async def test_request_exceptions(
    mocked: aioresponses,
    bring: Bring,
    exception: type[Exception],
) -> None:
    """Test exceptions."""
    mocked.clear()
    mocked.post("https://api.getbring.com/rest/v2/bringauth", exception=exception)
    with pytest.raises(BringRequestException):
        await bring.login()
