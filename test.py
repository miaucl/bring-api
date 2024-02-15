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
from bring_api.types import BringList

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
        logging.info("e-mail %s@gmail asserted as unknown.")

    # Test for known existing user
    if await bring.does_user_exist():
        logging.info("e-mail of known existing user asserted as valid")


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
        lists = (await bring.loadLists())["lists"]
        lst = next(lst for lst in lists if lst["name"] == os.environ["LIST"])
        logging.info("Selected list: %s (%s)", lst["name"], lst["listUuid"])

        await test_add_complete_remove(bring, lst)


asyncio.run(main())
