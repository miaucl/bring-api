"""Unit tests for bring-api."""
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


class TestNotifications:
    """Tests for notification method."""

    def test_notify_going_shopping(self, bring):
        """Test GOING_SHOPPING notification."""
