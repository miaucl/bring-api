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
