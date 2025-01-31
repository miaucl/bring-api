"""Tests for set_list_article_language method."""

import asyncio
from http import HTTPStatus

import aiohttp
from aioresponses import aioresponses
import pytest

from bring_api import Bring, BringAuthException, BringRequestException

from .conftest import UUID


@pytest.mark.usefixtures("mocked")
async def test_set_list_article_language(
    bring: Bring,
) -> None:
    """Test set list article language."""
    await bring.login()

    resp = await bring.set_list_article_language(UUID, "de-DE")
    assert resp.status == HTTPStatus.OK


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
        f"https://api.getbring.com/rest/bringusersettings/{UUID}/{UUID}/listArticleLanguage",
        exception=exception,
    )

    with pytest.raises(BringRequestException):
        await bring.set_list_article_language(UUID, "de-DE")


async def test_unauthorized(
    mocked: aioresponses,
    bring: Bring,
) -> None:
    """Test unauthorized exception."""
    await bring.login()
    mocked.clear()
    mocked.post(
        f"https://api.getbring.com/rest/bringusersettings/{UUID}/{UUID}/listArticleLanguage",
        status=HTTPStatus.UNAUTHORIZED,
    )

    with pytest.raises(BringAuthException):
        await bring.set_list_article_language(UUID, "de-DE")


async def test_value_error(
    bring: Bring,
) -> None:
    """Test ValueError exception."""

    with pytest.raises(ValueError):
        await bring.set_list_article_language(UUID, "es-CO")
