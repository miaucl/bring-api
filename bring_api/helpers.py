"""Helpers for the Bring API."""

import json
from typing import cast


def headers_serialize(headers: dict[str, str]) -> str:
    """Serialize all headers from the login session to a string for persistency.

    Parameters
    ----------
    headers
        The headers in the session to persist

    str
        The serialized data to persist

    """
    return json.dumps(headers)


def headers_deserialize(headers: str) -> dict[str, str]:
    """Deserialize all headers from the login session from a persisted string.

    Parameters
    ----------
    headers
        The persisted session headers as string

    Returns
    -------
    dict[str, str]
        The session cookies

    """
    return cast(dict[str, str], json.loads(headers))
