"""Unit tests for bring-api."""

import aiohttp
from aioresponses import aioresponses
from dotenv import load_dotenv
import pytest

from bring_api.bring import Bring

load_dotenv()
UUID = "00000000-00000000-00000000-00000000"

BRING_LOGIN_RESPONSE = {
    "uuid": UUID,
    "publicUuid": UUID,
    "email": "EMAIL",
    "name": "NAME",
    "photoPath": "",
    "bringListUUID": UUID,
    "access_token": "ACCESS_TOKEN",
    "refresh_token": "REFRESH_TOKEN",
    "token_type": "Bearer",
    "expires_in": 604799,
}

BRING_USER_ACCOUNT_RESPONSE = {"userLocale": {"language": "de", "country": "DE"}}

BRING_USER_SETTINGS_RESPONSE = {
    "usersettings": [],
    "userlistsettings": [
        {
            "listUuid": UUID,
            "usersettings": [{"key": "listArticleLanguage", "value": "de-DE"}],
        }
    ],
}

BRING_GET_LISTS_RESPONSE = {
    "lists": [
        {
            "listUuid": UUID,
            "name": "Einkauf",
            "theme": "ch.publisheria.bring.theme.home",
        },
    ]
}


@pytest.fixture(name="session")
async def aiohttp_client_session():
    """Create  a client session."""
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture(name="bring")
async def bring_api_client(session):
    """Create Bring instance."""
    bring = Bring(session, "EMAIL", "PASSWORD")
    return bring


@pytest.fixture(name="mocked")
def aioclient_mock():
    """Mock Aiohttp client requests."""
    with aioresponses() as m:
        yield m
