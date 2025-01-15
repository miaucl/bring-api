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


class BringTranslationException(BringException):
    """When translating an article fails."""


class BringMissingFieldException(Exception):
    """When a required field is missing in the response."""

    def __init__(self, e: Exception):
        """Initialize the exception.

        Parameters
        ----------
        e : Exception
            The original exception that was raised.

        """
        message = (
            f"Failed to parse error response: {str(e)} "
            "This is likely a bug. Please report it at: https://github.com/miaucl/bring-api/issues"
        )
        super().__init__(message)
