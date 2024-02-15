"""Bring API exceptions."""


class BringException(Exception):
    """General exception occurred."""

    pass


class BringAuthException(BringException):
    """When an authentication error is encountered."""

    pass


class BringRequestException(BringException):
    """When the HTTP request fails."""

    pass


class BringParseException(BringException):
    """When parsing the response of a request fails."""

    pass


class BringEMailInvalidException(BringException):
    """When checkemail returns emailValid false ."""


class BringUserUnknownException(BringException):
    """When checkemail returns userExists false."""
