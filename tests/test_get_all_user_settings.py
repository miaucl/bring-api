"""Tests for get_all_user_settings method."""

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
    BringTranslationException,
)

from .conftest import UUID, load_fixture


@pytest.mark.usefixtures("mocked")
async def test_get_all_user_settings(
    bring: Bring,
    snapshot: SnapshotAssertion,
) -> None:
    """Test for get_user_account."""
    await bring.login()
    data = await bring.get_all_user_settings()

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
        f"https://api.getbring.com/rest/bringusersettings/{UUID}",
        exception=exception,
    )

    with pytest.raises(BringRequestException):
        await bring.get_all_user_settings()


async def test_unauthorized(
    mocked: aioresponses,
    bring: Bring,
) -> None:
    """Test unauthorized exception."""
    await bring.login()
    mocked.clear()
    mocked.get(
        f"https://api.getbring.com/rest/bringusersettings/{UUID}",
        status=HTTPStatus.UNAUTHORIZED,
        body=load_fixture("error_response.json"),
    )

    with pytest.raises(BringAuthException):
        await bring.get_all_user_settings()


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
        f"https://api.getbring.com/rest/bringusersettings/{UUID}",
        status=status,
        body="not json",
        content_type="application/json",
    )

    with pytest.raises(exception):
        await bring.get_all_user_settings()


@pytest.mark.usefixtures("mocked")
async def test_load_user_list_settings(
    bring: Bring,
) -> None:
    """Test __load_user_list_settings."""

    await bring.login()
    data = await bring._Bring__load_user_list_settings()  # type: ignore[attr-defined]

    assert data[UUID]["listArticleLanguage"] == "de-DE"


async def test_load_user_list_settings_exception(
    bring: Bring,
) -> None:
    """Test __load_user_list_settings."""

    with (
        patch(
            "bring_api.Bring.get_all_user_settings", side_effect=BringRequestException
        ),
        pytest.raises(BringTranslationException),
    ):
        await bring._Bring__load_user_list_settings()  # type: ignore[attr-defined]
