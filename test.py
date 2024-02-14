"""Test script for Bring API."""
import asyncio
import logging
import os
import sys
import uuid

import aiohttp
from dotenv import load_dotenv

from bring_api.bring import Bring
from bring_api.types import BringItemOperation, BringList

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

load_dotenv()


async def test_add_complete_remove(bring: Bring, lst: BringList):
    """Test add-complete-remove for an item."""

    # Save an item with specifications to a certain shopping list
    await bring.saveItem(lst["listUuid"], "Äpfel", "low fat")

    # Get all the pending items of a list
    items = await bring.getItems(lst["listUuid"])
    logging.info("List purchase items: %s", items["purchase"])

    # Check of an item
    await bring.completeItem(lst["listUuid"], items["purchase"][0]["itemId"])

    # Get all the recent items of a list
    items = await bring.getItems(lst["listUuid"])
    logging.info("List recently items: %s", items["recently"])

    # Remove an item from a list
    await bring.removeItem(lst["listUuid"], "Äpfel")

    # Get all the items of a list
    items = await bring.getItems(lst["listUuid"])
    logging.info("List all items: %s / %s", items["purchase"], items["recently"])


async def test_batch_list_operations(bring: Bring, lst: BringList):
    """Test batch list operations."""

    # Add items with same name but different specifications
    item_uuid_1 = str(uuid.uuid4())
    item_uuid_2 = str(uuid.uuid4())
    add_items = [
        {
            "itemId": "Cilantro",
            "spec": "100g, dried",
            "uuid": item_uuid_1,
        },
        {
            "itemId": "Cilantro",
            "spec": "fresh",
            "uuid": item_uuid_2,
        },
    ]
    await bring.change_list(lst["listUuid"], add_items, BringItemOperation.ADD)

    # Get all the pending items of a list
    items = await bring.getItems(lst["listUuid"])
    logging.info("List purchase items: %s", items["purchase"])

    # Complete items on the list
    await bring.change_list(lst["listUuid"], add_items, BringItemOperation.COMPLETE)

    # Get all the recent items of a list
    items = await bring.getItems(lst["listUuid"])
    logging.info("List recently items: %s", items["recently"])

    # Remove items on the list
    await bring.change_list(lst["listUuid"], add_items, BringItemOperation.REMOVE)

    # Get all the items of a list
    items = await bring.getItems(lst["listUuid"])
    logging.info("List all items: %s / %s", items["purchase"], items["recently"])


async def main():
    """Test Bring API."""
    async with aiohttp.ClientSession() as session:
        # Create Bring instance with email and password
        bring = Bring(session, os.environ["EMAIL"], os.environ["PASSWORD"])
        # Login
        await bring.login()

        # Get information about all available shopping list and select one to test with
        lists = (await bring.loadLists())["lists"]
        lst = next(lst for lst in lists if lst["name"] == os.environ["LIST"])
        logging.info("Selected list: %s (%s)", lst["name"], lst["listUuid"])

        await test_add_complete_remove(bring, lst)

        await test_batch_list_operations(bring, lst)


asyncio.run(main())
