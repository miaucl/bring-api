"""Tests for get_all_user_settings method."""

from http import HTTPStatus
from unittest.mock import patch

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

from .conftest import UUID


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
