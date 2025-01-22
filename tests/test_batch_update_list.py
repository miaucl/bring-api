"""Tests for batch_update_list."""

from typing import Any

from aioresponses import aioresponses
import pytest

from bring_api import Bring, BringItem, BringItemOperation

from .conftest import DEFAULT_HEADERS, UUID


@pytest.mark.parametrize(
    ("item", "operation", "payload"),
    [
        (
            BringItem(itemId="item0", spec="spec", uuid=""),
            BringItemOperation.ADD,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item0",
                        "spec": "spec",
                        "uuid": "",
                        "operation": "TO_PURCHASE",
                    }
                ],
                "sender": "",
            },
        ),
        (
            BringItem(itemId="item1", spec="spec", uuid="uuid"),
            BringItemOperation.COMPLETE,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item1",
                        "spec": "spec",
                        "uuid": "uuid",
                        "operation": "TO_RECENTLY",
                    }
                ],
                "sender": "",
            },
        ),
        (
            BringItem(itemId="item2", spec="spec", uuid="uuid"),
            BringItemOperation.REMOVE,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item2",
                        "spec": "spec",
                        "uuid": "uuid",
                        "operation": "REMOVE",
                    }
                ],
                "sender": "",
            },
        ),
        (
            BringItem(
                itemId="item3",
                spec="spec",
                uuid="uuid",
                operation=BringItemOperation.ADD,
            ),
            None,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item3",
                        "spec": "spec",
                        "uuid": "uuid",
                        "operation": "TO_PURCHASE",
                    }
                ],
                "sender": "",
            },
        ),
        (
            BringItem(
                itemId="item4",
                spec="spec",
                uuid="uuid",
                operation=BringItemOperation.COMPLETE,
            ),
            None,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item4",
                        "spec": "spec",
                        "uuid": "uuid",
                        "operation": "TO_RECENTLY",
                    }
                ],
                "sender": "",
            },
        ),
        (
            BringItem(
                itemId="item5",
                spec="spec",
                uuid="uuid",
                operation=BringItemOperation.REMOVE,
            ),
            None,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item5",
                        "spec": "spec",
                        "uuid": "uuid",
                        "operation": "REMOVE",
                    }
                ],
                "sender": "",
            },
        ),
        (
            BringItem(
                itemId="item6",
                spec="spec",
                uuid="uuid",
                operation="TO_PURCHASE",
            ),
            None,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item6",
                        "spec": "spec",
                        "uuid": "uuid",
                        "operation": "TO_PURCHASE",
                    }
                ],
                "sender": "",
            },
        ),
        (
            BringItem(
                itemId="item7",
                spec="spec",
                uuid="uuid",
                operation="TO_RECENTLY",
            ),
            None,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item7",
                        "spec": "spec",
                        "uuid": "uuid",
                        "operation": "TO_RECENTLY",
                    }
                ],
                "sender": "",
            },
        ),
        (
            BringItem(
                itemId="item8",
                spec="spec",
                uuid="uuid",
                operation="REMOVE",
            ),
            None,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item8",
                        "spec": "spec",
                        "uuid": "uuid",
                        "operation": "REMOVE",
                    }
                ],
                "sender": "",
            },
        ),
        (
            BringItem(
                itemId="item9",
                spec="spec",
                uuid="uuid",
            ),
            None,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item9",
                        "spec": "spec",
                        "uuid": "uuid",
                        "operation": "TO_PURCHASE",
                    }
                ],
                "sender": "",
            },
        ),
        (
            BringItem(
                itemId="item10",
                spec="spec",
                uuid="uuid",
                operation=BringItemOperation.COMPLETE,
            ),
            BringItemOperation.ADD,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item10",
                        "spec": "spec",
                        "uuid": "uuid",
                        "operation": "TO_RECENTLY",
                    }
                ],
                "sender": "",
            },
        ),
        (
            BringItem(
                itemId="item11",
                spec="spec",
                uuid="uuid",
                operation=BringItemOperation.REMOVE,
            ),
            BringItemOperation.ADD,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item11",
                        "spec": "spec",
                        "uuid": "uuid",
                        "operation": "REMOVE",
                    }
                ],
                "sender": "",
            },
        ),
        (
            BringItem(itemId="item12", spec="", uuid=""),
            BringItemOperation.ADD,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item12",
                        "spec": "",
                        "uuid": "",
                        "operation": "TO_PURCHASE",
                    }
                ],
                "sender": "",
            },
        ),
        (
            BringItem(itemId="item13", spec="", uuid="uuid"),
            BringItemOperation.ADD,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item13",
                        "spec": "",
                        "uuid": "uuid",
                        "operation": "TO_PURCHASE",
                    }
                ],
                "sender": "",
            },
        ),
        (
            BringItem(itemId="item14", spec="spec", uuid=""),
            BringItemOperation.ADD,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item14",
                        "spec": "spec",
                        "uuid": "",
                        "operation": "TO_PURCHASE",
                    }
                ],
                "sender": "",
            },
        ),
        (
            BringItem(itemId="item15", spec="spec", uuid="uuid"),
            BringItemOperation.ADD,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item15",
                        "spec": "spec",
                        "uuid": "uuid",
                        "operation": "TO_PURCHASE",
                    }
                ],
                "sender": "",
            },
        ),
        (
            {"itemId": "item16", "spec": "spec", "uuid": "uuid"},
            BringItemOperation.ADD,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item16",
                        "spec": "spec",
                        "uuid": "uuid",
                        "operation": "TO_PURCHASE",
                    }
                ],
                "sender": "",
            },
        ),
    ],
)
async def test_batch_update_list_single_item(
    bring: Bring,
    mocked: aioresponses,
    item: BringItem,
    operation: BringItemOperation | None,
    payload: dict[str, Any],
) -> None:
    """Test batch_update_list."""
    await bring.login()
    await bring.batch_update_list(UUID, item, operation)

    mocked.assert_called_with(
        f"https://api.getbring.com/rest/v2/bringlists/{UUID}/items",
        method="PUT",
        headers=DEFAULT_HEADERS,
        json=payload,
    )


async def test_batch_update_list_multiple_items(
    bring: Bring,
    mocked: aioresponses,
) -> None:
    """Test batch_update_list."""
    test_items = [
        BringItem(
            itemId="item1",
            spec="spec1",
            uuid="uuid1",
            operation=BringItemOperation.ADD,
        ),
        BringItem(
            itemId="item2",
            spec="spec2",
            uuid="uuid2",
            operation=BringItemOperation.COMPLETE,
        ),
        BringItem(
            itemId="item3",
            spec="spec3",
            uuid="uuid3",
            operation=BringItemOperation.REMOVE,
        ),
    ]

    payload = {
        "changes": [
            {
                "accuracy": "0.0",
                "altitude": "0.0",
                "latitude": "0.0",
                "longitude": "0.0",
                "itemId": "item1",
                "spec": "spec1",
                "uuid": "uuid1",
                "operation": "TO_PURCHASE",
            },
            {
                "accuracy": "0.0",
                "altitude": "0.0",
                "latitude": "0.0",
                "longitude": "0.0",
                "itemId": "item2",
                "spec": "spec2",
                "uuid": "uuid2",
                "operation": "TO_RECENTLY",
            },
            {
                "accuracy": "0.0",
                "altitude": "0.0",
                "latitude": "0.0",
                "longitude": "0.0",
                "itemId": "item3",
                "spec": "spec3",
                "uuid": "uuid3",
                "operation": "REMOVE",
            },
        ],
        "sender": "",
    }
    await bring.login()
    await bring.batch_update_list(UUID, test_items)

    mocked.assert_called_with(
        f"https://api.getbring.com/rest/v2/bringlists/{UUID}/items",
        method="PUT",
        headers=DEFAULT_HEADERS,
        json=payload,
    )
