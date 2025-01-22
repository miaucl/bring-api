"""Tests for notification method."""

import enum
from typing import Any

from aioresponses import aioresponses
import pytest

from bring_api import ActivityType, Bring, BringNotificationType, ReactionType

from .conftest import DEFAULT_HEADERS, UUID


@pytest.mark.parametrize(
    ("notification_type", "item_name", "call_args"),
    [
        (
            BringNotificationType.GOING_SHOPPING,
            None,
            {
                "arguments": [],
                "listNotificationType": "GOING_SHOPPING",
                "senderPublicUserUuid": "00000000-0000-0000-0000-000000000000",
            },
        ),
        (
            BringNotificationType.CHANGED_LIST,
            None,
            {
                "arguments": [],
                "listNotificationType": "CHANGED_LIST",
                "senderPublicUserUuid": "00000000-0000-0000-0000-000000000000",
            },
        ),
        (
            BringNotificationType.SHOPPING_DONE,
            None,
            {
                "arguments": [],
                "listNotificationType": "SHOPPING_DONE",
                "senderPublicUserUuid": "00000000-0000-0000-0000-000000000000",
            },
        ),
        (
            BringNotificationType.URGENT_MESSAGE,
            "WITH_ITEM_NAME",
            {
                "arguments": ["WITH_ITEM_NAME"],
                "listNotificationType": "URGENT_MESSAGE",
                "senderPublicUserUuid": "00000000-0000-0000-0000-000000000000",
            },
        ),
    ],
)
async def test_notify(
    mocked: aioresponses,
    bring: Bring,
    notification_type: BringNotificationType,
    item_name: str | None,
    call_args: dict[str, Any],
) -> None:
    """Test GOING_SHOPPING notification."""
    await bring.login()
    await bring.notify(UUID, notification_type, item_name)

    mocked.assert_called_with(
        f"https://api.getbring.com/rest/v2/bringnotifications/lists/{UUID}",
        method="post",
        headers=DEFAULT_HEADERS,
        json=call_args,
        data=None,
    )


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
    await bring.login()
    await bring.notify(
        UUID,
        BringNotificationType.LIST_ACTIVITY_STREAM_REACTION,
        receiver=UUID,
        activity=UUID,
        activity_type=activity_type,
        reaction=reaction,
    )

    mocked.assert_called_with(
        f"https://api.getbring.com/rest/v2/bringnotifications/lists/{UUID}",
        method="post",
        headers=DEFAULT_HEADERS,
        json={
            "arguments": [],
            "listNotificationType": "LIST_ACTIVITY_STREAM_REACTION",
            "senderPublicUserUuid": "00000000-0000-0000-0000-000000000000",
            "receiverPublicUserUuid": "00000000-0000-0000-0000-000000000000",
            "listActivityStreamReaction": {
                "moduleUuid": "00000000-0000-0000-0000-000000000000",
                "moduleType": activity_type.value,
                "reactionType": reaction.value,
            },
        },
    )


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
