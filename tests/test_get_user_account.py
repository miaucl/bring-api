"""Tests for get_user_account method."""

from http import HTTPStatus

from aioresponses import aioresponses
import pytest
from syrupy.assertion import SnapshotAssertion

from bring_api import Bring, BringAuthException, BringParseException

from .conftest import UUID


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
