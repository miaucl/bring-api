"""Test script for Bring API."""
import asyncio
import logging
import os
import sys
import uuid

import aiohttp
from dotenv import load_dotenv

from bring_api.bring import Bring
from bring_api.exceptions import BringEMailInvalidException, BringUserUnknownException
from bring_api.types import BringItemOperation, BringList, BringNotificationType

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

load_dotenv()


async def test_add_complete_remove(bring: Bring, lst: BringList):
    """Test add-complete-remove for an item."""

    # Save an item with specifications to a certain shopping list
    await bring.save_item(lst["listUuid"], "Äpfel", "low fat")

    # Get all the pending items of a list
    items = await bring.get_list(lst["listUuid"])
    logging.info("List purchase items: %s", items["purchase"])

    # Check of an item
    await bring.complete_item(lst["listUuid"], items["purchase"][0]["itemId"])

    # Get all the recent items of a list
    items = await bring.get_list(lst["listUuid"])
    logging.info("List recently items: %s", items["recently"])

    # Remove an item from a list
    await bring.remove_item(lst["listUuid"], "Äpfel")

    # Get all the items of a list
    items = await bring.get_list(lst["listUuid"])
    logging.info("List all items: %s / %s", items["purchase"], items["recently"])


async def test_push_notifications(bring: Bring, lst: BringList):
    """Test sending push notifications."""

    # Send a going shopping notification
    await bring.notify(lst["listUuid"], BringNotificationType.GOING_SHOPPING)

    # Send a urgent message with argument item name
    await bring.notify(
        lst["listUuid"], BringNotificationType.URGENT_MESSAGE, "Pouletbrüstli"
    )


async def test_does_user_exist(bring: Bring):
    """Test does_user_exist."""

    rnd = str(uuid.uuid4())

    # Test invalid e-mail
    try:
        await bring.does_user_exist(f"{rnd}@gmail")
    except BringEMailInvalidException:
        logging.info("e-mail %s@gmail asserted as invalid.", rnd)

    # Test unknown user by generating random uuid
    try:
        await bring.does_user_exist(f"{rnd}@gmail.com")
    except BringUserUnknownException:
        logging.info("e-mail %s@gmail.com asserted as user unknown.", rnd)

    # Test for known existing user
    if await bring.does_user_exist():
        logging.info("e-mail %s asserted as valid and user exists", bring.mail)


async def test_translation(bring: Bring, lst: BringList):
    """Test article translations."""
    # Replace test list locale to get predictable results and
    # read back items with different locale asure catalog items where added correctly.
    locale_to = "de-DE"
    locale_from = "de-CH"

    locale_org = bring.user_list_settings[lst["listUuid"]]["listArticleLanguage"]

    test_items = {
        "Pouletbrüstli": "Hähnchenbrust",
        "Glacé": "Eis",
        "Zucchetti": "Zucchini",
        "Gipfeli": "Croissant",
        "Pelati": "Dosentomaten",
        "Fischstäbli": "Fischstäbchen",
        "Guetzli": "Plätzchen",
    }
    for k, v in test_items.items():
        # Save an item an item to
        bring.user_list_settings[lst["listUuid"]]["listArticleLanguage"] = locale_to
        await bring.save_item(lst["listUuid"], v)

        # Get all the pending items of a list
        bring.user_list_settings[lst["listUuid"]]["listArticleLanguage"] = locale_from
        items = await bring.get_list(lst["listUuid"])
        item = next(ii["itemId"] for ii in items["purchase"] if ii["itemId"] == k)
        assert item == k
        logging.info("Item: %s, translation: %s", v, item)

        await bring.remove_item(lst["listUuid"], k)

    # reset locale to original value for other tests
    bring.user_list_settings[lst["listUuid"]]["listArticleLanguage"] = locale_org


async def test_batch_list_operations(bring: Bring, lst: BringList):
    """Test batch list operations."""

    # Add items with same name but different specifications
    add_items = [
        {
            "itemId": "Cilantro",
            "spec": "100g, dried",
            "uuid": str(uuid.uuid4()),
        },
        {
            "itemId": "Cilantro",
            "spec": "fresh",
            "uuid": str(uuid.uuid4()),
        },
    ]

    await bring.batch_update_list(lst["listUuid"], add_items, BringItemOperation.ADD)
    logging.info("Add %s items to list %s", len(add_items), os.environ["LIST"])

    # Get all the pending items of a list
    items = await bring.get_list(lst["listUuid"])
    logging.info("List purchase items: %s", items["purchase"])

    # Complete items on the list
    await bring.batch_update_list(
        lst["listUuid"], add_items, BringItemOperation.COMPLETE
    )
    logging.info("Complete %s items on the list %s", len(add_items), os.environ["LIST"])

    # Get all the recent items of a list
    items = await bring.get_list(lst["listUuid"])
    logging.info("List recently items: %s", items["recently"])

    # Remove items on the list
    await bring.batch_update_list(lst["listUuid"], add_items, BringItemOperation.REMOVE)
    logging.info("Remove items from the list %s: %s", os.environ["LIST"], add_items)

    # Get all the items of a list
    items = await bring.get_list(lst["listUuid"])
    logging.info("List all items: %s / %s", items["purchase"], items["recently"])

    # Batch update list with add, complete and remove operations
    item1_uuid = str(uuid.uuid4())
    item2_uuid = str(uuid.uuid4())
    add_complete_delete_items = [
        {
            "itemId": "Hähnchen",
            "spec": "gegrillt",
            "uuid": item1_uuid,
            "operation": "TO_PURCHASE",
        },
        {
            "itemId": "Hähnchenbrust",
            "spec": "gebraten",
            "uuid": item2_uuid,
            "operation": "TO_PURCHASE",
        },
        {
            "itemId": "Hähnchen",
            "spec": "",
            "uuid": item1_uuid,
            "operation": "TO_RECENTLY",
        },
        {
            "itemId": "Hähnchenbrust",
            "spec": "",
            "uuid": item2_uuid,
            "operation": "TO_RECENTLY",
        },
        {
            "itemId": "Hähnchen",
            "spec": "",
            "uuid": item1_uuid,
            "operation": "REMOVE",
        },
        {
            "itemId": "Hähnchenbrust",
            "spec": "",
            "uuid": item2_uuid,
            "operation": "REMOVE",
        },
    ]
    await bring.batch_update_list(lst["listUuid"], add_complete_delete_items)
    logging.info(
        "Submit batch update with ADD, COMPLETE, REMOVE operations to list %s",
        os.environ["LIST"],
    )


async def main():
    """Test Bring API."""
    async with aiohttp.ClientSession() as session:
        # Create Bring instance with email and password
        bring = Bring(session, os.environ["EMAIL"], os.environ["PASSWORD"])

        # run before login
        await test_does_user_exist(bring)

        # Login
        await bring.login()

        # Get information about all available shopping list and select one to test with
        lists = (await bring.load_lists())["lists"]
        lst = next(lst for lst in lists if lst["name"] == os.environ["LIST"])
        logging.info("Selected list: %s (%s)", lst["name"], lst["listUuid"])

        await test_add_complete_remove(bring, lst)

        await test_push_notifications(bring, lst)

        await test_translation(bring, lst)

        await test_batch_list_operations(bring, lst)


asyncio.run(main())
