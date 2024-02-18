"""Unit tests for bring-api."""
import enum
import os
import secrets
import uuid

from dotenv import load_dotenv
import pytest

from bring_api.bring import Bring
from bring_api.exceptions import (
    BringAuthException,
    BringEMailInvalidException,
    BringUserUnknownException,
)
from bring_api.types import BringNotificationType

load_dotenv()


class TestDoesUserExist:
    """Tests for does_user_exist method."""

    async def test_mail_invalid(self, bring):
        """Test does_user_exist for invalid e-mail."""
        with pytest.raises(BringEMailInvalidException):
            rnd = secrets.token_urlsafe(48)
            await bring.does_user_exist(f"{rnd}@gmail")

    async def test_unknown_user(self, bring):
        """Test does_user_exist for unknown user."""
        with pytest.raises(BringUserUnknownException):
            rnd = secrets.token_urlsafe(48)
            await bring.does_user_exist(f"{rnd}@gmail.com")

    async def test_user_exist_with_parameter(self, bring):
        """Test does_user_exist for known user."""
        assert await bring.does_user_exist(os.environ["EMAIL"]) is True

    async def test_user_exist_without_parameter(self, bring):
        """Test does_user_exist for known user ."""
        assert await bring.does_user_exist() is True


class TestLogin:
    """Tests for login method."""

    async def test_mail_invalid(self, session):
        """Test login with invalid e-mail."""
        rnd = secrets.token_urlsafe(48)
        __bring = Bring(session, f"{rnd}@gmail", "")
        with pytest.raises(
            BringAuthException,
            match="Login failed due to bad request, please check your email.",
        ):
            await __bring.login()

    async def test_unauthorized(self, session):
        """Test login with unauthorized user."""
        rnd = secrets.token_urlsafe(48)
        __bring = Bring(session, f"{rnd}@gmail.com", rnd)
        with pytest.raises(
            BringAuthException,
            match="Login failed due to authorization failure, "
            "please check your email and password.",
        ):
            await __bring.login()

    async def test_successfull_login(self, bring):
        """Test login with valid user."""
        data = await bring.login()
        assert "access_token" in data
        assert "uuid" in data
        assert str(uuid.UUID(data["uuid"])) == data["uuid"], "uuid invalid"
        assert "publicUuid" in data
        assert str(uuid.UUID(data["publicUuid"])) == data["publicUuid"], "uuid invalid"


async def test_load_lists(bring):
    """Test load_lists."""
    await bring.login()
    lists = await bring.load_lists()
    assert isinstance(lists, dict) is True, "load_lists must return a TypedDict"
    assert len(lists["lists"]) > 0, "lists count is 0"
    assert next(
        (lst for lst in lists["lists"] if lst["name"] == os.environ["LIST"]), False
    ), f"Test List '{os.environ["LIST"]}' not found"
    for lst in lists["lists"]:
        assert (
            str(uuid.UUID(lst["listUuid"])) == lst["listUuid"]
        ), f"not a valid uuid {lst["listUuid"]}"
        assert len(lst["name"]) > 0, "name cannot be empty"


class TestNotifications:
    """Tests for notification method."""

    @pytest.mark.parametrize(
        ("notification_type", "item_name"),
        [
            (BringNotificationType.GOING_SHOPPING, ""),
            (BringNotificationType.CHANGED_LIST, ""),
            (BringNotificationType.SHOPPING_DONE, ""),
            (BringNotificationType.URGENT_MESSAGE, "WITH_ITEM_NAME"),
        ],
    )
    async def test_notify(
        self,
        bring,
        notification_type: BringNotificationType,
        item_name: str,
    ):
        """Test GOING_SHOPPING notification."""

        await bring.login()
        lists = (await bring.load_lists())["lists"]
        lst = next(lst for lst in lists if lst["name"] == os.environ["LIST"])
        resp = await bring.notify(lst["listUuid"], notification_type, item_name)
        assert resp.status == 200

    async def test_notify_urgent_message_item_name_missing(self, bring):
        """Test URGENT_MESSAGE notification."""

        await bring.login()
        lists = (await bring.load_lists())["lists"]
        lst = next(lst for lst in lists if lst["name"] == os.environ["LIST"])
        with pytest.raises(
            ValueError,
            match="notificationType is URGENT_MESSAGE but argument itemName missing.",
        ):
            await bring.notify(
                lst["listUuid"], BringNotificationType.URGENT_MESSAGE, ""
            )

    async def test_notify_notification_type_raise_attribute_error(self, bring):
        """Test URGENT_MESSAGE notification."""

        await bring.login()
        lists = (await bring.load_lists())["lists"]
        lst = next(lst for lst in lists if lst["name"] == os.environ["LIST"])
        with pytest.raises(
            AttributeError,
        ):
            await bring.notify(lst["listUuid"], "STRING", "")

    async def test_notify_notification_type_raise_type_error(self, bring):
        """Test URGENT_MESSAGE notification."""

        class WrongEnum(enum.Enum):
            """Test Enum."""

            UNKNOWN = "UNKNOWN"

        await bring.login()
        lists = (await bring.load_lists())["lists"]
        lst = next(lst for lst in lists if lst["name"] == os.environ["LIST"])
        with pytest.raises(
            TypeError,
            match="notificationType WrongEnum.UNKNOWN not supported,"
            "must be of type BringNotificationType.",
        ):
            await bring.notify(lst["listUuid"], WrongEnum.UNKNOWN, "")
