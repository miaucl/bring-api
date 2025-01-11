"""Smoke test for bring-api."""

import logging
import os

import aiohttp
from dotenv import load_dotenv
import pytest

from bring_api.bring import Bring
from bring_api.helpers import headers_deserialize, headers_serialize
from bring_api.types import BringList

load_dotenv()

_LOGGER = logging.getLogger(__name__)


def save_headers(headers: dict[str, str]) -> None:
    """Save the headers locally."""
    with open(".headers", "w", encoding="utf-8") as file:
        file.write(headers_serialize(headers))


def load_headers() -> dict[str, str]:
    """Load the headers locally."""
    # Open and read the file
    with open(".headers", encoding="utf-8") as file:
        return headers_deserialize(file.read() or "{}")


@pytest.fixture(name="headers")
async def cookies_str() -> dict[str, str]:
    """Load the headers."""

    return load_headers()


@pytest.fixture(name="session")
async def aiohttp_client_session():
    """Create  a client session."""
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture(name="bring")
async def bring_api_client(
    session: aiohttp.ClientSession, headers: dict[str, str]
) -> Bring:
    """Create Bring instance."""

    bring = Bring(session, os.environ["EMAIL"], os.environ["PASSWORD"])

    # Restore auth data from saved headers
    bring.headers = headers
    bring.uuid = headers["X-BRING-USER-UUID"]
    bring.public_uuid = headers["X-BRING-PUBLIC-USER-UUID"]
    await bring.reload_user_list_settings()
    await bring.reload_article_translations()

    return bring


@pytest.fixture(name="bring_no_auth")
async def bring_no_auth_api_client(session: aiohttp.ClientSession) -> Bring:
    """Create Bring instance."""

    bring = Bring(session, os.environ["EMAIL"], os.environ["PASSWORD"])

    return bring


@pytest.fixture(name="test_list")
async def test_list(bring: Bring) -> BringList:
    """Get the BringList instance to test with."""
    # Get information about all available shopping list and select the one to test with
    lists = (await bring.load_lists()).lists
    lst = next(lst for lst in lists if lst.name == os.environ["LIST"])
    _LOGGER.info("Selected list: %s (%s)", lst.name, lst.listUuid)
    return lst
