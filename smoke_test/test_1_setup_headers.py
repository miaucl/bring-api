"""Setup headers for smoke test for bring-api."""

import logging
import uuid

import pytest

from bring_api.bring import Bring
from bring_api.exceptions import BringEMailInvalidException, BringUserUnknownException
from smoke_test.conftest import save_headers

_LOGGER = logging.getLogger(__name__)


class TestSetupAndLogin:
    """Test setup and login."""

    async def test_does_user_exist(self, bring_no_auth: Bring):
        """Test does_user_exist."""

        rnd = str(uuid.uuid4())

        # Test invalid e-mail
        with pytest.raises(BringEMailInvalidException):
            await bring_no_auth.does_user_exist(f"{rnd}@gmail")
        _LOGGER.info("e-mail %s@gmail asserted as invalid.", rnd)

        # Test unknown user by generating random uuid
        with pytest.raises(BringUserUnknownException):
            await bring_no_auth.does_user_exist(f"{rnd}@gmail.com")
        _LOGGER.info("e-mail %s@gmail.com asserted as user unknown.", rnd)

        # Test for known existing user
        await bring_no_auth.does_user_exist()
        _LOGGER.info("e-mail %s asserted as valid and user exists", bring_no_auth.mail)

    async def test_bring_login(self, bring_no_auth: Bring) -> None:
        """Test bring login."""
        await bring_no_auth.login()
        _LOGGER.info("login for email %s successful", bring_no_auth.mail)
        save_headers(bring_no_auth.headers)
