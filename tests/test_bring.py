"""Unit tests for bring-api."""

import asyncio
import enum

import aiohttp
from dotenv import load_dotenv
import pytest

from bring_api.bring import Bring
from bring_api.exceptions import (
    BringAuthException,
    BringEMailInvalidException,
    BringParseException,
    BringRequestException,
    BringUserUnknownException,
)
from bring_api.types import BringNotificationType

from .conftest import (
    BRING_GET_LIST_RESPONSE,
    BRING_LOAD_LISTS_RESPONSE,
    BRING_LOGIN_RESPONSE,
    UUID,
    mocked__load_article_translations,
    mocked__load_user_list_settings,
    mocked_get_user_account,
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

    @pytest.mark.parametrize(
        ("exception", "expected"),
        [
            (asyncio.TimeoutError, BringRequestException),
            (aiohttp.ClientError, BringEMailInvalidException),
        ],
    )
    async def test_request_exception(self, mocked, bring, exception, expected):
        """Test request exceptions."""

        mocked.get(
            "https://api.getbring.com/rest/bringusers?email=EMAIL",
            exception=exception,
        )

        with pytest.raises(expected):
            await bring.does_user_exist("EMAIL")


class TestLogin:
    """Tests for login method."""

    async def test_mail_invalid(self, mocked, bring):
        """Test login with invalid e-mail."""
        mocked.post(
            "https://api.getbring.com/rest/v2/bringauth",
            status=400,
        )
        expected = "Login failed due to bad request, please check your email."
        with pytest.raises(BringAuthException, match=expected):
            await bring.login()

    async def test_unauthorized(self, mocked, bring):
        """Test login with unauthorized user."""
        mocked.post(
            "https://api.getbring.com/rest/v2/bringauth",
            status=401,
            payload={"message": ""},
        )
        expected = "Login failed due to authorization failure, please check your email and password."
        with pytest.raises(BringAuthException, match=expected):
            await bring.login()

    async def test_parse_exception(self, mocked, bring):
        """Test parse exceptions."""
        mocked.post(
            "https://api.getbring.com/rest/v2/bringauth",
            status=200,
            body="not json",
            headers={"content-type": "application/json"},
        )

        with pytest.raises(BringParseException):
            await bring.login()

    @pytest.mark.parametrize(
        "exception",
        [
            asyncio.TimeoutError,
            aiohttp.ClientError,
        ],
    )
    async def test_request_exceptions(self, mocked, bring, exception):
        """Test exceptions."""
        mocked.post("https://api.getbring.com/rest/v2/bringauth", exception=exception)
        with pytest.raises(BringRequestException):
            await bring.login()

    async def test_login(self, mocked, bring, monkeypatch):
        """Test login with valid user."""

        mocked.post(
            "https://api.getbring.com/rest/v2/bringauth",
            status=200,
            payload=BRING_LOGIN_RESPONSE,
        )

        monkeypatch.setattr(Bring, "get_user_account", mocked_get_user_account)
        monkeypatch.setattr(
            Bring, "_Bring__load_user_list_settings", mocked__load_user_list_settings
        )
        monkeypatch.setattr(
            Bring,
            "_Bring__load_article_translations",
            mocked__load_article_translations,
        )

        data = await bring.login()
        assert data == BRING_LOGIN_RESPONSE
        assert bring.headers["Authorization"] == "Bearer ACCESS_TOKEN"
        assert bring.headers["X-BRING-COUNTRY"] == "DE"
        assert bring.uuid == UUID
        assert bring.public_uuid == UUID
        assert bring.user_locale == "de-DE"


class TestLoadLists:
    """Tests for load_lists method."""

    async def test_load_lists(self, bring, mocked, monkeypatch):
        """Test load_lists."""

        mocked.get(
            f"https://api.getbring.com/rest/bringusers/{UUID}/lists",
            status=200,
            payload=BRING_LOAD_LISTS_RESPONSE,
        )
        monkeypatch.setattr(bring, "uuid", UUID)

        lists = await bring.load_lists()

        assert lists == BRING_LOAD_LISTS_RESPONSE

    async def test_parse_exception(self, mocked, bring, monkeypatch):
        """Test parse exceptions."""
        mocked.get(
            f"https://api.getbring.com/rest/bringusers/{UUID}/lists",
            status=200,
            body="not json",
            headers={"content-type": "application/json"},
        )
        monkeypatch.setattr(bring, "uuid", UUID)

        with pytest.raises(BringParseException):
            await bring.load_lists()

    @pytest.mark.parametrize(
        "exception",
        [
            asyncio.TimeoutError,
            aiohttp.ClientError,
        ],
    )
    async def test_request_exception(self, mocked, bring, exception, monkeypatch):
        """Test request exceptions."""
        mocked.get(
            f"https://api.getbring.com/rest/bringusers/{UUID}/lists",
            exception=exception,
        )
        monkeypatch.setattr(bring, "uuid", UUID)

        with pytest.raises(BringRequestException):
            await bring.load_lists()


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

    @pytest.mark.parametrize(
        "exception",
        [
            asyncio.TimeoutError,
            aiohttp.ClientError,
        ],
    )
    async def test_request_exception(self, mocked, bring, exception):
        """Test request exceptions."""

        mocked.post(
            f"https://api.getbring.com/rest/v2/bringnotifications/lists/{UUID}",
            exception=exception,
        )

        with pytest.raises(BringRequestException):
            await bring.notify(UUID, BringNotificationType.GOING_SHOPPING)


class TestGetList:
    """Tests for get_list method."""

    @pytest.mark.parametrize(
        "exception",
        [
            asyncio.TimeoutError,
            aiohttp.ClientError,
        ],
    )
    async def test_request_exception(self, mocked, bring, exception):
        """Test request exceptions."""

        mocked.get(
            f"https://api.getbring.com/rest/v2/bringlists/{UUID}",
            exception=exception,
        )

        with pytest.raises(BringRequestException):
            await bring.get_list(UUID)

    async def test_parse_exception(self, mocked, bring, monkeypatch):
        """Test parse exceptions."""
        mocked.get(
            f"https://api.getbring.com/rest/v2/bringlists/{UUID}",
            status=200,
            body="not json",
            headers={"content-type": "application/json"},
        )
        monkeypatch.setattr(bring, "uuid", UUID)

        with pytest.raises(BringParseException):
            await bring.get_list(UUID)

    async def test_get_list(self, mocked, bring, monkeypatch):
        """Test get list."""
        mocked.get(
            f"https://api.getbring.com/rest/v2/bringlists/{UUID}",
            status=200,
            payload=BRING_GET_LIST_RESPONSE,
        )

        def mocked_locale(*args, **kwargs) -> str:
            return "de-CH"

        monkeypatch.setattr(Bring, "_Bring__locale", mocked_locale)

        def mocked_translate(bring: Bring, item_id: str, *args, **kwargs) -> str:
            return item_id

        monkeypatch.setattr(Bring, "_Bring__translate", mocked_translate)
        monkeypatch.setattr(bring, "uuid", UUID)

        data = await bring.get_list(UUID)
        assert data == BRING_GET_LIST_RESPONSE["items"]
