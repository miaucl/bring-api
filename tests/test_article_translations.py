"""Unit tests for bring-api."""

import asyncio
from http import HTTPStatus
from unittest.mock import patch

import aiohttp
from aioresponses import aioresponses
import pytest
from syrupy.assertion import SnapshotAssertion

from bring_api import Bring, BringParseException, BringRequestException, UserLocale
from bring_api.const import BRING_SUPPORTED_LOCALES

from .conftest import UUID

"""Test loading of article translation tables."""


@pytest.mark.usefixtures("mocked")
def test_load_file(
    bring: Bring,
    snapshot: SnapshotAssertion,
) -> None:
    """Test loading json from file."""

    assert bring._Bring__load_article_translations_from_file("de-CH") == snapshot  # type: ignore[attr-defined]


@pytest.mark.usefixtures("mocked")
async def test_load_from_list_article_language(bring: Bring) -> None:
    """Test loading json from listArticleLanguage."""

    with patch.object(
        bring, "user_list_settings", {UUID: {"listArticleLanguage": "de-DE"}}
    ):
        dictionaries = await bring._Bring__load_article_translations()  # type: ignore[attr-defined]

    assert "de-DE" in dictionaries
    assert dictionaries["de-DE"]["Pouletbrüstli"] == "Hähnchenbrust"
    assert len(dictionaries["de-DE"]) == 444


async def test_load_from_user_locale(
    bring: Bring,
) -> None:
    """Test loading json from user_locale."""

    with patch.object(bring, "user_locale", "de-DE"):
        dictionaries = await bring._Bring__load_article_translations()  # type: ignore[attr-defined]

    assert "de-DE" in dictionaries
    assert dictionaries["de-DE"]["Pouletbrüstli"] == "Hähnchenbrust"
    assert len(dictionaries["de-DE"]) == 444


@pytest.mark.parametrize(
    ("test_locale", "expected_locale"),
    [
        ("de-XX", "de-DE"),
        ("en-XX", "en-US"),
        ("es-XX", "es-ES"),
        ("de-DE", "de-DE"),
        ("en-GB", "en-GB"),
    ],
)
async def test_map_user_language_to_locale(
    bring: Bring,
    test_locale: str,
    expected_locale: str,
) -> None:
    """Test mapping invalid user_locale to valid locale."""

    user_locale = UserLocale(language=test_locale[0:2], country=test_locale[3:5])
    locale = bring.map_user_language_to_locale(user_locale)

    assert expected_locale == locale


def test_get_locale_from_list(
    bring: Bring,
) -> None:
    """Test get locale from list."""
    with (
        patch.object(bring, "user_locale", "es-ES"),
        patch.object(
            bring,
            "user_list_settings",
            {UUID: {"listArticleLanguage": "de-DE"}},
        ),
    ):
        locale = bring._Bring__locale(UUID)  # type: ignore[attr-defined]

    assert locale == "de-DE"


def test_get_locale_from_user(
    bring: Bring,
) -> None:
    """Test get locale from user_locale."""
    with (
        patch.object(bring, "user_locale", "es-ES"),
        patch.object(
            bring,
            "user_list_settings",
            {UUID: {"listArticleLanguage": "de-DE"}},
        ),
    ):
        locale = bring._Bring__locale("xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx")  # type: ignore[attr-defined]

    assert locale == "es-ES"


def test_get_locale_from_list_fallback(
    bring: Bring,
) -> None:
    """Test get locale from list and fallback to user_locale."""
    with (
        patch.object(bring, "user_locale", "es-ES"),
        patch.object(bring, "user_list_settings", {UUID: {}}),
    ):
        locale = bring._Bring__locale(UUID)  # type: ignore[attr-defined]

    assert locale == "es-ES"


async def test_load_all_locales(
    bring: Bring,
) -> None:
    """Test loading all locales."""

    user_list_settings = {
        k: {"listArticleLanguage": v} for k, v in enumerate(BRING_SUPPORTED_LOCALES)
    }

    with patch.object(bring, "user_list_settings", user_list_settings):
        dictionaries = await bring._Bring__load_article_translations()  # type: ignore[attr-defined]

    assert len(dictionaries) == 19  # de-CH is skipped


async def test_load_fallback_to_download(
    bring: Bring,
    mocked: aioresponses,
) -> None:
    """Test loading json and fallback to download from web."""
    mocked.get(
        "https://web.getbring.com/locale/articles.de-DE.json",
        payload={"test": "test"},
        status=HTTPStatus.OK,
    )
    with patch("builtins.open", side_effect=OSError):
        await bring.login()

    assert bring._Bring__translations["de-DE"] == {"test": "test"}  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "exception",
    [
        asyncio.TimeoutError,
        aiohttp.ClientError,
    ],
)
async def test_request_exceptions(
    bring: Bring,
    mocked: aioresponses,
    exception: type[Exception],
) -> None:
    """Test loading json and fallback to download from web."""
    mocked.get(
        "https://web.getbring.com/locale/articles.de-DE.json", exception=exception
    )

    with (
        patch.object(bring, "user_locale", "de-DE"),
        patch("builtins.open", side_effect=OSError),
        pytest.raises(BringRequestException),
    ):
        await bring._Bring__load_article_translations()  # type: ignore[attr-defined]


async def test_parse_exception(
    bring: Bring,
    mocked: aioresponses,
) -> None:
    """Test loading json and fallback to download from web."""
    mocked.get(
        "https://web.getbring.com/locale/articles.de-DE.json",
        status=HTTPStatus.OK,
        body="not json",
        content_type="application/json",
    )

    with (
        patch.object(bring, "user_locale", "de-DE"),
        patch("builtins.open", side_effect=OSError),
        pytest.raises(BringParseException),
    ):
        await bring._Bring__load_article_translations()  # type: ignore[attr-defined]
