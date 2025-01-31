"""Tests for does_user_exist method."""

import asyncio
from http import HTTPStatus

import aiohttp
from aioresponses import aioresponses
import pytest

from bring_api import (
    Bring,
    BringEMailInvalidException,
    BringRequestException,
    BringUserUnknownException,
)


async def test_mail_invalid(
    mock_aiohttp: aioresponses,
    bring: Bring,
) -> None:
    """Test does_user_exist for invalid e-mail."""
    mock_aiohttp.get(
        "https://api.getbring.com/rest/bringusers?email=EMAIL",
        status=HTTPStatus.BAD_REQUEST,
    )
    with pytest.raises(BringEMailInvalidException):
        await bring.does_user_exist("EMAIL")


async def test_unknown_user(
    mock_aiohttp: aioresponses,
    bring: Bring,
) -> None:
    """Test does_user_exist for unknown user."""
    mock_aiohttp.get(
        "https://api.getbring.com/rest/bringusers?email=EMAIL",
        status=HTTPStatus.NOT_FOUND,
    )
    with pytest.raises(BringUserUnknownException):
        await bring.does_user_exist("EMAIL")


async def test_mail_value_error(
    mock_aiohttp: aioresponses,
    bring: Bring,
) -> None:
    """Test does_user_exist value error."""
    mock_aiohttp.get(
        "https://api.getbring.com/rest/bringusers?email=",
        status=HTTPStatus.OK,
    )
    setattr(bring, "mail", None)

    with pytest.raises(ValueError, match="Argument mail missing."):
        await bring.does_user_exist()


async def test_user_exist_with_parameter(
    mock_aiohttp: aioresponses,
    bring: Bring,
) -> None:
    """Test does_user_exist for known user."""
    mock_aiohttp.get(
        "https://api.getbring.com/rest/bringusers?email=EMAIL",
        status=HTTPStatus.OK,
    )
    assert await bring.does_user_exist("EMAIL") is True


async def test_user_exist_without_parameter(
    mock_aiohttp: aioresponses,
    bring: Bring,
) -> None:
    """Test does_user_exist for known user."""
    mock_aiohttp.get(
        "https://api.getbring.com/rest/bringusers?email=EMAIL",
        status=HTTPStatus.OK,
    )
    assert await bring.does_user_exist() is True


@pytest.mark.parametrize(
    ("exception", "expected"),
    [
        (asyncio.TimeoutError, BringRequestException),
        (aiohttp.ClientError, BringEMailInvalidException),
    ],
)
async def test_request_exception(
    mock_aiohttp: aioresponses,
    bring: Bring,
    exception: type[Exception],
    expected: type[Exception],
) -> None:
    """Test request exceptions."""

    mock_aiohttp.get(
        "https://api.getbring.com/rest/bringusers?email=EMAIL",
        exception=exception,
    )

    with pytest.raises(expected):
        await bring.does_user_exist("EMAIL")
