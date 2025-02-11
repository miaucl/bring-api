"""Unit tests for bring-api."""

from collections.abc import AsyncGenerator, Generator
from functools import lru_cache
from http import HTTPStatus
import pathlib

import aiohttp
from aioresponses import aioresponses
from dotenv import load_dotenv
import pytest

from bring_api import Bring

load_dotenv()
UUID = "00000000-0000-0000-0000-000000000000"


DEFAULT_HEADERS = {
    "Authorization": "Bearer ACCESS_TOKEN",
    "X-BRING-API-KEY": "cof4Nc6D8saplXjE3h3HXqHH8m7VU2i1Gs0g85Sp",
    "X-BRING-CLIENT": "android",
    "X-BRING-APPLICATION": "bring",
    "X-BRING-COUNTRY": "DE",
    "X-BRING-USER-UUID": "00000000-0000-0000-0000-000000000000",
    "X-BRING-PUBLIC-USER-UUID": "00000000-0000-0000-0000-000000000000",
}


@lru_cache
def load_fixture(filename: str) -> str:
    """Load a fixture."""

    return (
        pathlib.Path(__file__)
        .parent.joinpath("fixtures", filename)
        .read_text(encoding="utf-8")
    )


@pytest.fixture(name="headers")
async def headers() -> str:
    """Load the headers."""

    # Open and read the file
    with open("tests/test.headers", encoding="utf-8") as file:
        return file.read()


@pytest.fixture(name="session")
async def aiohttp_client_session() -> AsyncGenerator[aiohttp.ClientSession]:
    """Create  a client session."""
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture(name="bring")
async def bring_api_client(session: aiohttp.ClientSession) -> Bring:
    """Create Bring instance."""
    bring = Bring(session, "EMAIL", "PASSWORD")
    bring._expires_at = 604799

    return bring


@pytest.fixture
def mock_aiohttp() -> Generator[aioresponses]:
    """Mock Aiohttp client."""
    with aioresponses() as m:
        yield m


@pytest.fixture(name="mocked")
def aioclient_mock() -> Generator[aioresponses]:
    """Mock Bring API requests."""
    with aioresponses() as m:
        m.post(
            "https://api.getbring.com/rest/v2/bringauth",
            status=HTTPStatus.OK,
            body=load_fixture("login_response.json"),
        )
        m.get(
            f"https://api.getbring.com/rest/v2/bringusers/{UUID}",
            status=HTTPStatus.OK,
            body=load_fixture("user_account_response.json"),
            repeat=True,
        )
        m.get(
            f"https://api.getbring.com/rest/bringusersettings/{UUID}",
            status=HTTPStatus.OK,
            body=load_fixture("user_settings_response.json"),
            repeat=True,
        )
        m.get(
            f"https://api.getbring.com/rest/bringusers/{UUID}/lists",
            status=HTTPStatus.OK,
            body=load_fixture("load_lists_response.json"),
        )
        m.post(
            f"https://api.getbring.com/rest/v2/bringnotifications/lists/{UUID}",
            status=HTTPStatus.OK,
        )
        m.get(
            f"https://api.getbring.com/rest/v2/bringlists/{UUID}",
            status=HTTPStatus.OK,
            body=load_fixture("get_list_response.json"),
            repeat=True,
        )
        m.get(
            f"https://api.getbring.com/rest/bringlists/{UUID}/details",
            status=HTTPStatus.OK,
            body=load_fixture("item_details_response.json"),
        )
        m.put(
            f"https://api.getbring.com/rest/v2/bringlists/{UUID}/items",
            status=HTTPStatus.OK,
        )
        m.post(
            "https://api.getbring.com/rest/v2/bringauth/token",
            status=HTTPStatus.OK,
            body=load_fixture("token_response.json"),
            repeat=True,
        )
        m.get(
            f"https://api.getbring.com/rest/v2/bringlists/{UUID}/activity",
            status=HTTPStatus.OK,
            body=load_fixture("activity_response.json"),
        )
        m.get(
            f"https://api.getbring.com/rest/v2/bringlists/{UUID}/users",
            status=HTTPStatus.OK,
            body=load_fixture("list_users_response.json"),
        )
        m.post(
            f"https://api.getbring.com/rest/bringusersettings/{UUID}/{UUID}/listArticleLanguage",
            status=HTTPStatus.OK,
        )
        m.get(
            "https://api.getbring.com/rest/bringrecipes/parser?url=https://example.com",
            status=HTTPStatus.OK,
            body=load_fixture("recipe.json"),
        )
        m.post(
            "https://api.getbring.com/rest/v2/bringtemplates",
            status=HTTPStatus.CREATED,
            body=load_fixture("create_recipe_response.json"),
        )
        m.delete(
            "https://api.getbring.com/rest/v2/bringtemplates/98ad5860-e8d2-4e3f-8c9e-0fe3f59eec8a",
            status=HTTPStatus.NO_CONTENT,
        )
        yield m
