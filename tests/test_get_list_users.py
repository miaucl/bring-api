"""Tests for get_list_users method."""

from http import HTTPStatus

from aioresponses import aioresponses
import pytest
from syrupy.assertion import SnapshotAssertion

from bring_api import Bring, BringAuthException, BringParseException

from .conftest import UUID


@pytest.mark.usefixtures("mocked")
async def test_get_lists_users(
    bring: Bring,
    snapshot: SnapshotAssertion,
) -> None:
    """Test get_list_users."""

    await bring.login()
    activity = await bring.get_list_users(UUID)

    assert activity == snapshot


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
        f"https://api.getbring.com/rest/v2/bringlists/{UUID}/users",
        status=status,
        body="not json",
        content_type="application/json",
    )

    with pytest.raises(exception):
        await bring.get_list_users(UUID)
