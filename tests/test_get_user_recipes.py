"""Unit tests for get_user_recipes."""

import pytest
from syrupy.assertion import SnapshotAssertion

from bring_api import Bring


@pytest.mark.usefixtures("mocked")
async def test_get_user_recipes(
    bring: Bring,
    snapshot: SnapshotAssertion,
) -> None:
    """Test get_user_recipes."""
    await bring.login()
    result = await bring.get_user_recipes()
    assert result == snapshot
