"""Bring API exceptions."""


class BringException(Exception):
    """General exception occurred."""


class BringAuthException(BringException):
    """When an authentication error is encountered."""


class BringRequestException(BringException):
    """When the HTTP request fails."""


class BringParseException(BringException):
    """When parsing the response of a request fails."""


class BringEMailInvalidException(BringException):
    """When checkemail returns emailValid false ."""


class BringUserUnknownException(BringException):
    """When checkemail returns userExists false."""
