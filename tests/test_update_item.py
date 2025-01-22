"""Test for save_item method."""

import asyncio
from typing import Any

import aiohttp
from aioresponses import aioresponses
import pytest

from bring_api import Bring, BringRequestException

from .conftest import DEFAULT_HEADERS, UUID


@pytest.mark.parametrize(
    ("item_name", "specification", "item_uuid", "payload"),
    [
        (
            "item name",
            "",
            None,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item name",
                        "spec": "",
                        "uuid": None,
                        "operation": "TO_PURCHASE",
                    }
                ],
                "sender": "",
            },
        ),
        (
            "item name",
            "specification",
            None,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item name",
                        "spec": "specification",
                        "uuid": None,
                        "operation": "TO_PURCHASE",
                    }
                ],
                "sender": "",
            },
        ),
        (
            "item name",
            "",
            UUID,
            {
                "changes": [
                    {
                        "accuracy": "0.0",
                        "altitude": "0.0",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "itemId": "item name",
                        "spec": "",
                        "uuid": UUID,
                        "operation": "TO_PURCHASE",
                    }
                ],
                "sender": "",
            },
        ),
    ],
)
async def test_update_item(
    mocked: aioresponses,
    bring: Bring,
    item_name: str,
    specification: str,
    item_uuid: str | None,
    payload: dict[str, Any],
) -> None:
    """Test save_item."""
    await bring.login()

    await bring.update_item(UUID, item_name, specification, item_uuid)

    mocked.assert_called_with(
        f"https://api.getbring.com/rest/v2/bringlists/{UUID}/items",
        method="PUT",
        headers=DEFAULT_HEADERS,
        json=payload,
    )


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
    mocked.put(
        f"https://api.getbring.com/rest/v2/bringlists/{UUID}/items",
        exception=exception,
    )

    with pytest.raises(BringRequestException) as exc:
        await bring.update_item(UUID, "item_name", "specification")
    assert (
        exc.value.args[0] == f"Updating item item_name (specification) in list {UUID} "
        "failed due to request exception."
    )
