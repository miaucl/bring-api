"""Tests for get_inspiration."""

import pytest
from syrupy.assertion import SnapshotAssertion

from bring_api import Bring


@pytest.mark.usefixtures("mocked")
async def test_get_inspirations(
    bring: Bring,
    snapshot: SnapshotAssertion,
) -> None:
    """Test get_inspirations."""
    await bring.login()
    result = await bring.get_inspirations("mine")

    assert result == snapshot


@pytest.mark.usefixtures("mocked")
async def test_get_inspiration_filters(
    bring: Bring,
    snapshot: SnapshotAssertion,
) -> None:
    """Test get_inspirations."""
    await bring.login()
    result = await bring.get_inspiration_filters()

    assert result == snapshot
