"""Smoke test for bring-api."""

import logging
import uuid

from dotenv import load_dotenv

from bring_api.bring import Bring
from bring_api.types import BringItemOperation, BringList, BringNotificationType

load_dotenv()

_LOGGER = logging.getLogger(__name__)


class TestMethods:
    """Test methods."""

    async def test_add_complete_remove(
        self, bring: Bring, test_list: BringList
    ) -> None:
        """Test add-complete-remove for an item."""

        # Save an item with specifications to a certain shopping list
        await bring.save_item(test_list.listUuid, "Äpfel", "low fat")

        # Get all the pending items of a list
        items = (await bring.get_list(test_list.listUuid)).items
        _LOGGER.info("List purchase items: %s", items.purchase)

        # Check of an item
        await bring.complete_item(test_list.listUuid, items.purchase[0].itemId)

        # Get all the recent items of a list
        items = (await bring.get_list(test_list.listUuid)).items
        _LOGGER.info("List recently items: %s", items.recently)

        # Remove an item from a list
        await bring.remove_item(test_list.listUuid, "Äpfel")

        # Get all the items of a list
        items = (await bring.get_list(test_list.listUuid)).items
        _LOGGER.info("List all items: %s / %s", items.purchase, items.recently)

    async def test_push_notifications(self, bring: Bring, test_list: BringList) -> None:
        """Test sending push notifications."""

        # Send a going shopping notification
        await bring.notify(test_list.listUuid, BringNotificationType.GOING_SHOPPING)

        # Send a urgent message with argument item name
        await bring.notify(
            test_list.listUuid, BringNotificationType.URGENT_MESSAGE, "Pouletbrüstli"
        )

    async def test_translation(self, bring: Bring, test_list: BringList) -> None:
        """Test article translations."""
        # Replace test list locale to get predictable results and
        # read back items with different locale asure catalog items where added correctly.
        locale_to = "de-DE"
        locale_from = "de-CH"

        locale_org = bring.user_list_settings[str(test_list.listUuid)].get(
            "listArticleLanguage", bring.user_locale
        )

        test_items = {
            "Pouletbrüstli": "Hähnchenbrust",
            "Glacé": "Eis",
            "Zucchetti": "Zucchini",
            "Gipfeli": "Croissant",
            "Pelati": "Dosentomaten",
            "Fischstäbli": "Fischstäbchen",
            "Guetzli": "Plätzchen",
            "Paprika": "Paprika",
        }
        for k, v in test_items.items():
            # Save an item an item to
            bring.user_list_settings[str(test_list.listUuid)]["listArticleLanguage"] = (
                locale_to
            )
            await bring.save_item(test_list.listUuid, v)

            # Get all the pending items of a list
            bring.user_list_settings[str(test_list.listUuid)]["listArticleLanguage"] = (
                locale_from
            )
            items = await bring.get_list(test_list.listUuid)
            item = next(ii.itemId for ii in items.items.purchase if ii.itemId == k)
            assert item == k
            _LOGGER.info("Item: %s, translation: %s", v, item)

            await bring.remove_item(test_list.listUuid, k)

        # reset locale to original value for other tests
        bring.user_list_settings[str(test_list.listUuid)]["listArticleLanguage"] = (
            locale_org
        )

    async def test_batch_list_operations(
        self, bring: Bring, test_list: BringList
    ) -> None:
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

        await bring.batch_update_list(
            test_list.listUuid, add_items, BringItemOperation.ADD
        )
        _LOGGER.info("Add %s items to list %s", len(add_items), test_list.name)

        # Get all the pending items of a list
        items = (await bring.get_list(test_list.listUuid)).items
        _LOGGER.info("List purchase items: %s", items.purchase)

        # Complete items on the list
        await bring.batch_update_list(
            test_list.listUuid, add_items, BringItemOperation.COMPLETE
        )
        _LOGGER.info("Complete %s items on the list %s", len(add_items), test_list.name)

        # Get all the recent items of a list
        items = (await bring.get_list(test_list.listUuid)).items
        _LOGGER.info("List recently items: %s", items.recently)

        # Remove items on the list
        await bring.batch_update_list(
            test_list.listUuid, add_items, BringItemOperation.REMOVE
        )
        _LOGGER.info("Remove items from the list %s: %s", test_list.name, add_items)

        # Get all the items of a list
        items = (await bring.get_list(test_list.listUuid)).items
        _LOGGER.info("List all items: %s / %s", items.purchase, items.recently)

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
        await bring.batch_update_list(test_list.listUuid, add_complete_delete_items)
        _LOGGER.info(
            "Submit batch update with ADD, COMPLETE, REMOVE operations to list %s",
            test_list.name,
        )

    async def test_article_language(self, bring: Bring, test_list: BringList) -> None:
        """Test article language."""
        await bring.set_list_article_language(test_list.listUuid, "es-ES")
        await bring.get_list(test_list.listUuid)
        await bring.set_list_article_language(test_list.listUuid, "de-DE")
