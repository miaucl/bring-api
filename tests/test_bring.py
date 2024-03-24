"""Unit tests for bring-api."""

import asyncio
import enum
from unittest.mock import patch

import aiohttp
from dotenv import load_dotenv
import pytest

from bring_api.exceptions import (
    BringAuthException,
    BringEMailInvalidException,
    BringRequestException,
    BringUserUnknownException,
)
from bring_api.types import BringNotificationType

from .conftest import (
    BRING_GET_LISTS_RESPONSE,
    BRING_LOGIN_RESPONSE,
    BRING_USER_ACCOUNT_RESPONSE,
    BRING_USER_SETTINGS_RESPONSE,
    UUID,
)

load_dotenv()


class TestDoesUserExist:
    """Tests for does_user_exist method."""

    async def test_mail_invalid(self, mocked, bring):
        """Test does_user_exist for invalid e-mail."""
        mocked.get("https://api.getbring.com/rest/bringusers?email=EMAIL", status=400)
        with pytest.raises(BringEMailInvalidException):
            await bring.does_user_exist("EMAIL")

    async def test_unknown_user(self, mocked, bring):
        """Test does_user_exist for unknown user."""
        mocked.get("https://api.getbring.com/rest/bringusers?email=EMAIL", status=404)
        with pytest.raises(BringUserUnknownException):
            await bring.does_user_exist("EMAIL")

    async def test_user_exist_with_parameter(self, mocked, bring):
        """Test does_user_exist for known user."""
        mocked.get("https://api.getbring.com/rest/bringusers?email=EMAIL", status=200)
        assert await bring.does_user_exist("EMAIL") is True

    async def test_user_exist_without_parameter(self, mocked, bring):
        """Test does_user_exist for known user."""
        mocked.get(
            "https://api.getbring.com/rest/bringusers?email=EMAIL",
            status=200,
        )
        assert await bring.does_user_exist() is True


class TestLogin:
    """Tests for login method."""

    async def test_mail_invalid(self, mocked, bring):
        """Test login with invalid e-mail."""
        mocked.post(
            "https://api.getbring.com/rest/v2/bringauth",
            status=400,
        )
        with pytest.raises(
            BringAuthException,
            match="Login failed due to bad request, please check your email.",
        ):
            await bring.login()

    async def test_unauthorized(self, mocked, bring):
        """Test login with unauthorized user."""
        mocked.post(
            "https://api.getbring.com/rest/v2/bringauth",
            status=401,
            payload={"message": ""},
        )
        with pytest.raises(
            BringAuthException,
            match="Login failed due to authorization failure, "
            "please check your email and password.",
        ):
            await bring.login()

    @pytest.mark.parametrize(
        "exception",
        [
            asyncio.TimeoutError,
            aiohttp.ClientError,
        ],
    )
    async def test_exceptions(self, mocked, bring, exception):
        """Test exceptions."""
        mocked.post("https://api.getbring.com/rest/v2/bringauth", exception=exception)
        with pytest.raises(BringRequestException):
            await bring.login()

    async def test_successfull_login(self, mocked, bring):
        """Test login with valid user."""

        mocked.post(
            "https://api.getbring.com/rest/v2/bringauth",
            status=200,
            payload=BRING_LOGIN_RESPONSE,
        )
        mocked.get(
            f"https://api.getbring.com/rest/v2/bringusers/{UUID}",
            status=200,
            payload=BRING_USER_ACCOUNT_RESPONSE,
        )
        mocked.get(
            f"https://api.getbring.com/rest/bringusersettings/{UUID}",
            status=200,
            payload=BRING_USER_SETTINGS_RESPONSE,
        )

        await bring.login()

        assert bring.headers["Authorization"] == "Bearer ACCESS_TOKEN"
        assert bring.uuid == UUID
        assert bring.public_uuid == UUID
        assert bring.user_locale == "de-DE"
        assert bring.user_list_settings[UUID]["listArticleLanguage"] == "de-DE"


async def test_load_lists(bring, mocked):
    """Test load_lists."""

    mocked.get(
        f"https://api.getbring.com/rest/bringusers/{UUID}/lists",
        status=200,
        payload=BRING_GET_LISTS_RESPONSE,
    )
    with patch.object(bring, "uuid", UUID):
        lists = await bring.load_lists()
        assert isinstance(lists, dict) is True, "load_lists must return a TypedDict"
        assert len(lists["lists"]) > 0, "lists count is 0"


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
        mocked,
    ):
        """Test GOING_SHOPPING notification."""

        mocked.post(
            f"https://api.getbring.com/rest/v2/bringnotifications/lists/{UUID}",
            status=200,
        )
        resp = await bring.notify(UUID, notification_type, item_name)
        assert resp.status == 200

    async def test_notify_urgent_message_item_name_missing(self, bring, mocked):
        """Test URGENT_MESSAGE notification."""
        mocked.post(
            f"https://api.getbring.com/rest/v2/bringnotifications/lists/{UUID}",
            status=200,
        )
        with pytest.raises(
            ValueError,
            match="notificationType is URGENT_MESSAGE but argument itemName missing.",
        ):
            await bring.notify(UUID, BringNotificationType.URGENT_MESSAGE, "")

    async def test_notify_notification_type_raise_attribute_error(self, bring, mocked):
        """Test URGENT_MESSAGE notification."""

        with pytest.raises(
            AttributeError,
        ):
            await bring.notify(UUID, "STRING", "")

    async def test_notify_notification_type_raise_type_error(self, bring, mocked):
        """Test URGENT_MESSAGE notification."""

        class WrongEnum(enum.Enum):
            """Test Enum."""

            UNKNOWN = "UNKNOWN"

        with pytest.raises(
            TypeError,
            match="notificationType WrongEnum.UNKNOWN not supported,"
            "must be of type BringNotificationType.",
        ):
            await bring.notify(UUID, WrongEnum.UNKNOWN, "")
