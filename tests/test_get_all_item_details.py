"""Test for get_all_item_details method."""

from http import HTTPStatus

from aioresponses import aioresponses
import pytest
from syrupy.assertion import SnapshotAssertion

from bring_api import (
    Bring,
    BringAuthException,
    BringParseException,
    BringRequestException,
)

from .conftest import UUID


@pytest.mark.usefixtures("mocked")
async def test_get_all_item_details(
    bring: Bring,
    snapshot: SnapshotAssertion,
) -> None:
    """Test get_all_item_details."""
    await bring.login()
    data = await bring.get_all_item_details(UUID)
    assert data == snapshot


async def test_list_not_found(
    mocked: aioresponses,
    bring: Bring,
) -> None:
    """Test get_all_item_details."""
    await bring.login()
    mocked.clear()
    mocked.get(
        f"https://api.getbring.com/rest/bringlists/{UUID}/details",
        status=HTTPStatus.NOT_FOUND,
        reason=f"List with uuid '{UUID}' not found",
    )

    with pytest.raises(BringRequestException):
        await bring.get_all_item_details(UUID)


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
        f"https://api.getbring.com/rest/bringlists/{UUID}/details",
        status=status,
        body="not json",
        content_type="application/json",
    )

    with pytest.raises(exception):
        await bring.get_all_item_details(UUID)
