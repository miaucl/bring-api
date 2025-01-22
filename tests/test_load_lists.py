"""Tests for load_lists method."""

from http import HTTPStatus

from aioresponses import aioresponses
import pytest
from syrupy.assertion import SnapshotAssertion

from bring_api import Bring, BringAuthException, BringParseException

from .conftest import UUID


@pytest.mark.usefixtures("mocked")
async def test_load_lists(
    bring: Bring,
    snapshot: SnapshotAssertion,
) -> None:
    """Test load_lists."""
    await bring.login()
    lists = await bring.load_lists()

    assert lists == snapshot


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
        f"https://api.getbring.com/rest/bringusers/{UUID}/lists",
        status=status,
        body="not json",
        content_type="application/json",
    )

    with pytest.raises(exception):
        await bring.load_lists()
