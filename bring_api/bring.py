"""Bring api implementation."""
import asyncio
from json import JSONDecodeError
import logging
import traceback
from typing import Optional, cast

import aiohttp

from .exceptions import (
    BringAuthException,
    BringEMailInvalidException,
    BringParseException,
    BringRequestException,
    BringUserUnknownException,
)
from .types import (
    BringAuthResponse,
    BringItemsResponse,
    BringListItemDetails,
    BringListItemsDetailsResponse,
    BringListResponse,
    BringNotificationsConfigType,
    BringNotificationType,
)

_LOGGER = logging.getLogger(__name__)


class Bring:
    """Unofficial Bring API interface."""

    def __init__(
        self, session: aiohttp.ClientSession, mail: str, password: str
    ) -> None:
        """Init function for Bring API."""
        self._session = session

        self.mail = mail
        self.password = password
        self.uuid = ""
        self.public_uuid = ""

        self.url = "https://api.getbring.com/rest/"

        self.headers = {
            "Authorization": "Bearer",
            "X-BRING-API-KEY": "cof4Nc6D8saplXjE3h3HXqHH8m7VU2i1Gs0g85Sp",
            "X-BRING-CLIENT": "android",
            "X-BRING-APPLICATION": "bring",
            "X-BRING-COUNTRY": "DE",
            "X-BRING-USER-UUID": "",
        }

    async def login(self) -> BringAuthResponse:
        """Try to login.

        Returns
        -------
        Response
            The server response object.

        Raises
        ------
        BringRequestException
            If the request fails.
        BringParseException
            If the parsing of the request response fails.
        BringAuthException
            If the login fails due to missing data in the API response.
            You should check your email and password.

        """
        user_data = {"email": self.mail, "password": self.password}

        try:
            url = f"{self.url}v2/bringauth"
            async with self._session.post(url, data=user_data) as r:
                _LOGGER.debug("Response from %s: %s", url, r.status)

                if r.status == 401:
                    try:
                        errmsg = await r.json()
                    except JSONDecodeError:
                        _LOGGER.error(
                            "Exception: Cannot parse login request response:\n %s",
                            traceback.format_exc(),
                        )
                    else:
                        _LOGGER.error("Exception: Cannot login: %s", errmsg["message"])
                    raise BringAuthException(
                        "Login failed due to authorization failure, "
                        "please check your email and password."
                    )
                if r.status == 400:
                    _LOGGER.error("Exception: Cannot login: %s", await r.text())
                    raise BringAuthException(
                        "Login failed due to bad request, please check your email."
                    )
                r.raise_for_status()

                try:
                    data = cast(
                        BringAuthResponse,
                        {
                            key: val
                            for key, val in (await r.json()).items()
                            if key in BringAuthResponse.__annotations__
                        },
                    )
                except JSONDecodeError as e:
                    _LOGGER.error(
                        "Exception: Cannot login:\n %s", traceback.format_exc()
                    )
                    raise BringParseException(
                        "Cannot parse login request response."
                    ) from e
        except asyncio.TimeoutError as e:
            _LOGGER.error("Exception: Cannot login:\n %s", traceback.format_exc())
            raise BringRequestException(
                "Authentication failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.error("Exception: Cannot login:\n %s", traceback.format_exc())
            raise BringRequestException(
                "Authentication failed due to request exception."
            ) from e

        if "uuid" not in data or "access_token" not in data:
            _LOGGER.error("Exception: Cannot login: Data missing in API response.")
            raise BringAuthException(
                "Login failed due to missing data in the API response,"
                "please check your email and password."
            )

        self.uuid = data["uuid"]
        self.public_uuid = data.get("publicUuid", "")
        self.headers["X-BRING-USER-UUID"] = self.uuid
        self.headers["Authorization"] = f'Bearer {data["access_token"]}'

        return data

    async def load_lists(self) -> BringListResponse:
        """Load all shopping lists.

        Returns
        -------
        dict

        The JSON response as a dict.

        Raises
        ------
        BringRequestException
            If the request fails.
        BringParseException
            If the parsing of the request response fails.

        """
        try:
            url = f"{self.url}bringusers/{self.uuid}/lists"
            async with self._session.get(url, headers=self.headers) as r:
                _LOGGER.debug("Response from %s: %s", url, r.status)
                r.raise_for_status()

                try:
                    data = cast(
                        BringListResponse,
                        {
                            key: val
                            for key, val in (await r.json()).items()
                            if key in BringListResponse.__annotations__
                        },
                    )
                    return data
                except JSONDecodeError as e:
                    _LOGGER.error(
                        "Exception: Cannot get lists:\n %s", traceback.format_exc()
                    )
                    raise BringParseException(
                        "Loading lists failed during parsing of request response."
                    ) from e
        except asyncio.TimeoutError as e:
            _LOGGER.error("Exception: Cannot get lists:\n %s", traceback.format_exc())
            raise BringRequestException(
                "Loading list failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.error("Exception: Cannot get lists:\n %s", traceback.format_exc())
            raise BringRequestException(
                "Loading lists failed due to request exception."
            ) from e

    async def get_list(self, list_uuid: str) -> BringItemsResponse:
        """Get all items from a shopping list.

        Parameters
        ----------
        list_uuid : str
            A list uuid returned by loadLists()

        Returns
        -------
        dict
            The JSON response as a dict.

        Raises
        ------
        BringRequestException
            If the request fails.
        BringParseException
            If the parsing of the request response fails.

        """
        try:
            url = f"{self.url}v2/bringlists/{list_uuid}"
            async with self._session.get(url, headers=self.headers) as r:
                _LOGGER.debug("Response from %s: %s", url, r.status)
                r.raise_for_status()

                try:
                    data = cast(
                        BringItemsResponse,
                        {
                            key: val
                            for key, val in (await r.json())["items"].items()
                            if key in BringItemsResponse.__annotations__
                        },
                    )
                    return data
                except JSONDecodeError as e:
                    _LOGGER.error(
                        "Exception: Cannot get items for list %s:\n%s",
                        list_uuid,
                        traceback.format_exc(),
                    )
                    raise BringParseException(
                        "Loading list items failed during parsing of request response."
                    ) from e
        except asyncio.TimeoutError as e:
            _LOGGER.error(
                "Exception: Cannot get items for list %s:\n%s",
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                "Loading list items failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.error(
                "Exception: Cannot get items for list %s:\n%s",
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                "Loading list items failed due to request exception."
            ) from e

    async def get_all_item_details(
        self, list_uuid: str
    ) -> BringListItemsDetailsResponse:
        """Get all details from a shopping list.

        Parameters
        ----------
        list_uuid : str
            A list uuid returned by loadLists()

        Returns
        -------
        list
            The JSON response as a list. A list of item details.
            Caution: This is NOT a list of the items currently marked as 'to buy'.
            See getItems() for that.
            This contains the items that where customized by changing
            their default icon, category or uploading an image.

        Raises
        ------
        BringRequestException
            If the request fails.
        BringParseException
            If the parsing of the request response fails.

        """
        try:
            url = f"{self.url}bringlists/{list_uuid}/details"
            async with self._session.get(url, headers=self.headers) as r:
                _LOGGER.debug("Response from %s: %s", url, r.status)
                r.raise_for_status()

                try:
                    data = [
                        cast(
                            BringListItemDetails,
                            {
                                key: val
                                for key, val in item.items()
                                if key in BringListItemDetails.__annotations__
                            },
                        )
                        for item in (await r.json())["items"]
                    ]
                    return cast(BringListItemsDetailsResponse, data)
                except JSONDecodeError as e:
                    _LOGGER.error(
                        "Exception: Cannot get item details for list %s:\n%s",
                        list_uuid,
                        traceback.format_exc(),
                    )
                    raise BringParseException(
                        "Loading list details failed during parsing of request response."
                    ) from e
        except asyncio.TimeoutError as e:
            _LOGGER.error(
                "Exception: Cannot get item details for list %s:\n%s",
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                "Loading list details failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.error(
                "Exception: Cannot get item details for list %s:\n%s",
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                "Loading list details failed due to request exception."
            ) from e

    async def save_item(
        self, list_uuid: str, item_name: str, specification: str = ""
    ) -> aiohttp.ClientResponse:
        """Save an item to a shopping list.

        Parameters
        ----------
        list_uuid : str
            A list uuid returned by loadLists()
        item_name : str
            The name of the item you want to save.
        specification : str, optional
            The details you want to add to the item.

        Returns
        -------
        Response
            The server response object.

        Raises
        ------
        BringRequestException
            If the request fails.

        """
        data = {
            "purchase": item_name,
            "specification": specification,
        }
        try:
            url = f"{self.url}v2/bringlists/{list_uuid}"
            async with self._session.put(url, headers=self.headers, data=data) as r:
                _LOGGER.debug("Response from %s: %s", url, r.status)
                r.raise_for_status()
                return r
        except asyncio.TimeoutError as e:
            _LOGGER.error(
                "Exception: Cannot save item %s (%s) to list %s:\n%s",
                item_name,
                specification,
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                f"Saving item {item_name} ({specification}) to list {list_uuid}"
                "failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.error(
                "Exception: Cannot save item %s (%s) to list %s:\n%s",
                item_name,
                specification,
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                f"Saving item {item_name} ({specification}) to list {list_uuid}"
                "failed due to request exception."
            ) from e

    async def update_item(
        self, list_uuid: str, item_name: str, specification: str = ""
    ) -> aiohttp.ClientResponse:
        """Update an existing list item.

        Parameters
        ----------
        list_uuid : str
            A list uuid returned by loadLists()
        item_name : str
            The name of the item you want to update.
        specification : str, optional
            The details you want to update on the item.

        Returns
        -------
        Response
            The server response object.

        Raises
        ------
        BringRequestException
            If the request fails.

        """
        data = {"purchase": item_name, "specification": specification}
        try:
            url = f"{self.url}v2/bringlists/{list_uuid}"
            async with self._session.put(url, headers=self.headers, data=data) as r:
                _LOGGER.debug("Response from %s: %s", url, r.status)
                r.raise_for_status()
                return r
        except asyncio.TimeoutError as e:
            _LOGGER.error(
                "Exception: Cannot update item %s (%s) to list %s:\n%s",
                item_name,
                specification,
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                f"Updating item {item_name} ({specification}) in list {list_uuid}"
                "failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.error(
                "Exception: Cannot update item %s (%s) to list %s:\n%s",
                item_name,
                specification,
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                f"Updating item {item_name} ({specification}) in list {list_uuid}"
                "failed due to request exception."
            ) from e

    async def remove_item(
        self, list_uuid: str, item_name: str
    ) -> aiohttp.ClientResponse:
        """Remove an item from a shopping list.

        Parameters
        ----------
        list_uuid : str
            A list uuid returned by loadLists()
        item_name : str
            The name of the item you want to remove.

        Returns
        -------
        Response
            The server response object.

        Raises
        ------
        BringRequestException
            If the request fails.

        """
        data = {
            "remove": item_name,
        }
        try:
            url = f"{self.url}v2/bringlists/{list_uuid}"
            async with self._session.put(url, headers=self.headers, data=data) as r:
                _LOGGER.debug("Response from %s: %s", url, r.status)
                r.raise_for_status()
                return r
        except asyncio.TimeoutError as e:
            _LOGGER.error(
                "Exception: Cannot delete item %s from list %s:\n%s",
                item_name,
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                f"Removing item {item_name} from list {list_uuid}"
                "failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.error(
                "Exception: Cannot delete item %s from list %s:\n%s",
                item_name,
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                f"Removing item {item_name} from list {list_uuid}"
                "failed due to request exception."
            ) from e

    async def complete_item(
        self, list_uuid: str, item_name: str
    ) -> aiohttp.ClientResponse:
        """Complete an item from a shopping list. This will add it to recent items.

        If it was not on the list, it will still be added to recent items.

        Parameters
        ----------
        list_uuid : str
            A list uuid returned by loadLists()
        item_name : str
            The name of the item you want to complete.

        Returns
        -------
        Response
            The server response object.

        Raises
        ------
        BringRequestException
            If the request fails.

        """
        data = {"recently": item_name}
        try:
            url = f"{self.url}v2/bringlists/{list_uuid}"
            async with self._session.put(url, headers=self.headers, data=data) as r:
                _LOGGER.debug("Response from %s: %s", url, r.status)
                r.raise_for_status()
                return r
        except asyncio.TimeoutError as e:
            _LOGGER.error(
                "Exception: Cannot complete item %s in list %s:\n%s",
                item_name,
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                f"Completing item {item_name} from list {list_uuid}"
                "failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.error(
                "Exception: Cannot complete item %s in list %s:\n%s",
                item_name,
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                f"Completing item {item_name} from list {list_uuid}"
                "failed due to request exception."
            ) from e

    async def notify(
        self,
        list_uuid: str,
        notification_type: BringNotificationType,
        item_name: str,
    ) -> aiohttp.ClientResponse:
        """Send a push notification to all other members of a shared list.

        Parameters
        ----------
        list_uuid : str
            A list uuid returned by loadLists()
        notification_type : BringNotificationType
            The type of notification to be sent
        item_name : str, optional
            The text that **must** be included in the URGENT_MESSAGE BringNotificationType.

        Returns
        -------
        Response
            The server response object.

        Raises
        ------
        BringRequestException
            If the request fails.

        """
        json = BringNotificationsConfigType(
            arguments=[],
            listNotificationType=notification_type.value,
            senderPublicUserUuid=self.public_uuid,
        )

        if not isinstance(notification_type, BringNotificationType):
            _LOGGER.error(
                "Exception: notificationType %s not supported.", notification_type
            )
            raise TypeError(
                f"notificationType {notification_type} not supported,"
                "must be of type BringNotificationType."
            )
        if notification_type is BringNotificationType.URGENT_MESSAGE:
            if not item_name or len(item_name) == 0:
                _LOGGER.error("Exception: Argument itemName missing.")
                raise ValueError(
                    "notificationType is URGENT_MESSAGE but argument itemName missing."
                )

            json["arguments"] = [item_name]
        try:
            url = f"{self.url}v2/bringnotifications/lists/{list_uuid}"
            async with self._session.post(url, headers=self.headers, json=json) as r:
                _LOGGER.debug("Response from %s: %s", url, r.status)
                r.raise_for_status()
                return r
        except asyncio.TimeoutError as e:
            _LOGGER.error(
                "Exception: Cannot send notification %s for list %s:\n%s",
                notification_type,
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                f"Sending notification {notification_type} for list {list_uuid}"
                "failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.error(
                "Exception: Cannot send notification %s for list %s:\n%s",
                notification_type,
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                f"Sending notification {notification_type} for list {list_uuid}"
                "failed due to request exception."
            ) from e

    async def does_user_exist(self, mail: Optional[str] = None) -> bool:
        """Check if e-mail is valid and user exists.

        Parameters
        ----------
        mail : str
            An e-mail address.

        Returns
        -------
        bool
            True if user exists.

        Raises
        ------
        BringRequestException
            If the request fails.
        BringEMailInvalidException
            If the email is invalid.
        BringUserUnknownException
            If the user is does not exist

        """
        mail = mail or self.mail

        if not mail:
            raise ValueError("Argument mail missing.")

        params = {"email": mail}

        try:
            url = f"{self.url}bringusers"
            async with self._session.get(url, headers=self.headers, params=params) as r:
                _LOGGER.debug("Response from %s: %s", url, r.status)

                if r.status == 404:
                    _LOGGER.error("Exception: User %s does not exist.", mail)
                    raise BringUserUnknownException(f"User {mail} does not exist.")

                r.raise_for_status()

        except asyncio.TimeoutError as e:
            _LOGGER.error(
                "Exception: Cannot get verification for %s:\n%s",
                mail,
                traceback.format_exc(),
            )
            raise BringRequestException(
                "Verifying email failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.error(
                "Exception: E-mail %s is invalid.",
                mail,
            )
            raise BringEMailInvalidException(f"E-mail {mail} is invalid.") from e

        return True
