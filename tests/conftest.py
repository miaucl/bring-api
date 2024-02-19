"""Unit tests for bring-api."""
import os

import aiohttp
from dotenv import load_dotenv
import pytest

from bring_api.bring import Bring

load_dotenv()


@pytest.fixture
async def session():
    """Create  a client session."""
    async with aiohttp.ClientSession() as __session:
        yield __session


@pytest.fixture
async def bring(session):
    """Create Bring instance."""
    __bring = Bring(session, os.environ["EMAIL"], os.environ["PASSWORD"])
    return __bring
