"""Tests for parse_recipe."""

import pytest
from syrupy.assertion import SnapshotAssertion

from bring_api import Bring, BringRecipe

from .conftest import load_fixture


@pytest.mark.usefixtures("mocked")
async def test_parse_recipe(
    bring: Bring,
    snapshot: SnapshotAssertion,
) -> None:
    """Test parse_recipe."""
    await bring.login()
    result = await bring.parse_recipe("https://example.com")

    assert result == snapshot


@pytest.mark.usefixtures("mocked")
async def test_create_recipe(
    bring: Bring,
    snapshot: SnapshotAssertion,
) -> None:
    """Test create_recipe."""
    await bring.login()

    recipe = BringRecipe.from_json(load_fixture("recipe.json"))
    result = await bring.create_recipe(recipe)

    assert result == snapshot


@pytest.mark.usefixtures("mocked")
async def test_delete_recipe(
    bring: Bring,
    snapshot: SnapshotAssertion,
) -> None:
    """Test delete_recipe."""
    await bring.login()

    await bring.delete_recipe("98ad5860-e8d2-4e3f-8c9e-0fe3f59eec8a")
