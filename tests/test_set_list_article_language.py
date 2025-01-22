"""Tests for set_list_article_language method."""

from aioresponses import aioresponses
import pytest

from bring_api import Bring

from .conftest import DEFAULT_HEADERS, UUID


async def test_set_list_article_language(
    mocked: aioresponses,
    bring: Bring,
) -> None:
    """Test set list article language."""
    await bring.login()

    await bring.set_list_article_language(UUID, "de-DE")
    mocked.assert_called_with(
        f"https://api.getbring.com/rest/bringusersettings/{UUID}/{UUID}/listArticleLanguage",
        method="POST",
        headers=DEFAULT_HEADERS,
        data={"value": "de-DE"},
    )


async def test_value_error(
    bring: Bring,
) -> None:
    """Test ValueError exception."""

    with pytest.raises(ValueError):
        await bring.set_list_article_language(UUID, "es-CO")
