"""Unit tests for get_template_content."""

import pytest
from syrupy.assertion import SnapshotAssertion

from bring_api import Bring


@pytest.mark.usefixtures("mocked")
async def test_get_template_content(
    bring: Bring,
    snapshot: SnapshotAssertion,
) -> None:
    """Test get_template_content."""
    await bring.login()
    result = await bring.get_template_content("1f80e479-f04b-4dfa-98fb-bee670536fe8")
    assert result == snapshot
