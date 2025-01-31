"""Test for __translate method."""

from unittest.mock import patch

import pytest

from bring_api import Bring, BringTranslationException


def test_translate_to_locale(
    bring: Bring,
) -> None:
    """Test __translate with to_locale."""
    with patch.object(
        bring, "_Bring__translations", {"de-DE": {"Pouletbrüstli": "Hähnchenbrust"}}
    ):
        item = bring._Bring__translate("Pouletbrüstli", to_locale="de-DE")  # type: ignore[attr-defined]

    assert item == "Hähnchenbrust"


def test_translate_from_locale(bring: Bring) -> None:
    """Test __translate with from_locale."""
    with patch.object(
        bring, "_Bring__translations", {"de-DE": {"Pouletbrüstli": "Hähnchenbrust"}}
    ):
        item = bring._Bring__translate("Hähnchenbrust", from_locale="de-DE")  # type: ignore[attr-defined]

    assert item == "Pouletbrüstli"


def test_translate_value_error_no_locale(bring: Bring) -> None:
    """Test __translate with missing locale argument."""
    with pytest.raises(
        ValueError,
        match="One of the arguments from_locale or to_locale required.",
    ):
        bring._Bring__translate("item_name")  # type: ignore[attr-defined]


def test_translate_value_error_unsupported_locale(bring: Bring) -> None:
    """Test __translate with unsupported locale."""
    locale = "en-ES"
    with pytest.raises(ValueError, match=f"Locale {locale} not supported by Bring."):
        bring._Bring__translate("item_name", from_locale=locale)  # type: ignore[attr-defined]


def test_translate_exception(bring: Bring) -> None:
    """Test __translate BringTranslationException."""
    with pytest.raises(BringTranslationException):
        bring._Bring__translate("item_name", from_locale="de-DE")  # type: ignore[attr-defined]
