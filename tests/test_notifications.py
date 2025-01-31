"""Tests for notification method."""

import asyncio
import enum
from http import HTTPStatus

import aiohttp
from aioresponses import aioresponses
import pytest

from bring_api import (
    ActivityType,
    Bring,
    BringAuthException,
    BringNotificationType,
    BringRequestException,
    ReactionType,
)

from .conftest import UUID, load_fixture


@pytest.mark.parametrize(
    ("notification_type", "item_name"),
    [
        (BringNotificationType.GOING_SHOPPING, None),
        (BringNotificationType.CHANGED_LIST, None),
        (BringNotificationType.SHOPPING_DONE, None),
        (BringNotificationType.URGENT_MESSAGE, "WITH_ITEM_NAME"),
    ],
)
@pytest.mark.usefixtures("mocked")
async def test_notify(
    bring: Bring,
    notification_type: BringNotificationType,
    item_name: str | None,
) -> None:
    """Test GOING_SHOPPING notification."""

    resp = await bring.notify(UUID, notification_type, item_name)
    assert resp.status == HTTPStatus.OK


@pytest.mark.parametrize(
    "activity_type",
    [
        ActivityType.LIST_ITEMS_REMOVED,
        ActivityType.LIST_ITEMS_ADDED,
        ActivityType.LIST_ITEMS_CHANGED,
    ],
)
@pytest.mark.parametrize(
    "reaction",
    [
        ReactionType.THUMBS_UP,
        ReactionType.MONOCLE,
        ReactionType.DROOLING,
        ReactionType.HEART,
    ],
)
async def test_notify_activity_stream_reaction(
    bring: Bring,
    mocked: aioresponses,
    activity_type: ActivityType,
    reaction: ReactionType,
) -> None:
    """Test GOING_SHOPPING notification."""

    resp = await bring.notify(
        UUID,
        BringNotificationType.LIST_ACTIVITY_STREAM_REACTION,
        receiver=UUID,
        activity=UUID,
        activity_type=activity_type,
        reaction=reaction,
    )
    assert resp.status == HTTPStatus.OK


@pytest.mark.usefixtures("mocked")
async def test_notify_urgent_message_item_name_missing(
    bring: Bring,
) -> None:
    """Test URGENT_MESSAGE notification."""

    with pytest.raises(
        ValueError,
        match="notificationType is URGENT_MESSAGE but argument itemName missing.",
    ):
        await bring.notify(UUID, BringNotificationType.URGENT_MESSAGE, "")


@pytest.mark.usefixtures("mocked")
async def test_notify_notification_type_raise_attribute_error(
    bring: Bring,
) -> None:
    """Test URGENT_MESSAGE notification."""

    with pytest.raises(
        AttributeError,
    ):
        await bring.notify(UUID, "STRING", "")  # type: ignore[arg-type]


@pytest.mark.usefixtures("mocked")
async def test_notify_notification_type_raise_type_error(
    bring: Bring,
) -> None:
    """Test URGENT_MESSAGE notification."""

    class WrongEnum(enum.Enum):
        """Test Enum."""

        UNKNOWN = "UNKNOWN"

    with pytest.raises(
        TypeError,
        match="notificationType WrongEnum.UNKNOWN not supported,"
        "must be of type BringNotificationType.",
    ):
        await bring.notify(UUID, WrongEnum.UNKNOWN, "")  # type: ignore[arg-type]


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
    mocked.clear()
    mocked.post(
        f"https://api.getbring.com/rest/v2/bringnotifications/lists/{UUID}",
        exception=exception,
    )

    with pytest.raises(BringRequestException):
        await bring.notify(UUID, BringNotificationType.GOING_SHOPPING)


async def test_unauthorized(
    mocked: aioresponses,
    bring: Bring,
) -> None:
    """Test unauthorized exception."""
    mocked.clear()
    mocked.post(
        f"https://api.getbring.com/rest/v2/bringnotifications/lists/{UUID}",
        status=HTTPStatus.UNAUTHORIZED,
        body=load_fixture("error_response.json"),
    )
    with pytest.raises(BringAuthException):
        await bring.notify(UUID, BringNotificationType.GOING_SHOPPING)


async def test_parse_exception(
    mocked: aioresponses,
    bring: Bring,
) -> None:
    """Test parse exceptions."""
    mocked.clear()
    mocked.post(
        f"https://api.getbring.com/rest/v2/bringnotifications/lists/{UUID}",
        status=HTTPStatus.UNAUTHORIZED,
        body="not json",
        content_type="application/json",
    )

    with pytest.raises(BringAuthException):
        await bring.notify(UUID, BringNotificationType.GOING_SHOPPING)
