"""Bring api implementation."""

import asyncio
from http import HTTPStatus
import json
from json import JSONDecodeError
import logging
import os
import time
import traceback
from typing import List, Optional, cast

import aiohttp

from .const import (
    API_BASE_URL,
    BRING_DEFAULT_LOCALE,
    BRING_SUPPORTED_LOCALES,
    DEFAULT_HEADERS,
    LOCALES_BASE_URL,
    MAP_LANG_TO_LOCALE,
)
from .exceptions import (
    BringAuthException,
    BringEMailInvalidException,
    BringParseException,
    BringRequestException,
    BringTranslationException,
    BringUserUnknownException,
)
from .types import (
    BringAuthResponse,
    BringAuthTokenRespone,
    BringItem,
    BringItemOperation,
    BringItemsResponse,
    BringListItemDetails,
    BringListItemsDetailsResponse,
    BringListResponse,
    BringNotificationsConfigType,
    BringNotificationType,
    BringSyncCurrentUserResponse,
    BringUserListSettingEntry,
    BringUserSettingsEntry,
    BringUserSettingsResponse,
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

        self.public_uuid = ""
        self.user_list_settings: dict[str, dict[str, str]] = {}
        self.user_locale = BRING_DEFAULT_LOCALE

        self.__translations: dict[str, dict[str, str]] = {}
        self.uuid = ""

        self.url = API_BASE_URL

        self.headers = DEFAULT_HEADERS.copy()

        self.loop = asyncio.get_running_loop()
        self.refresh_token = ""
        self.__expires_in: int

    @property
    def expires_in(self) -> int:
        """Refresh token expiration."""
        return max(0, self.__expires_in - int(time.time()))

    @expires_in.setter
    def expires_in(self, expires_in: int | str) -> None:
        self.__expires_in = int(time.time()) + int(expires_in)

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
            If the login fails due invalid credentials.
            You should check your email and password.

        """
        user_data = {"email": self.mail, "password": self.password}

        try:
            url = f"{self.url}v2/bringauth"
            async with self._session.post(url, data=user_data) as r:
                _LOGGER.debug(
                    "Response from %s [%s]: %s",
                    url,
                    r.status,
                    await r.text()
                    if r.status != 200
                    else "",  # do not log response on success, as it contains sensible data
                )

                if r.status == HTTPStatus.UNAUTHORIZED:
                    try:
                        errmsg = await r.json()
                    except JSONDecodeError as e:
                        _LOGGER.debug(
                            "Exception: Cannot parse login request response:\n %s",
                            traceback.format_exc(),
                        )
                        raise BringParseException(
                            "Login failed due to authorization failure "
                            "but error response could not be parsed."
                        ) from e
                    _LOGGER.debug("Exception: Cannot login: %s", errmsg["message"])
                    raise BringAuthException(
                        "Login failed due to authorization failure, "
                        "please check your email and password."
                    )
                if r.status == HTTPStatus.BAD_REQUEST:
                    _LOGGER.debug("Exception: Cannot login: %s", await r.text())
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
                    _LOGGER.debug(
                        "Exception: Cannot login:\n %s", traceback.format_exc()
                    )
                    raise BringParseException(
                        "Cannot parse login request response."
                    ) from e
        except asyncio.TimeoutError as e:
            _LOGGER.debug("Exception: Cannot login:\n %s", traceback.format_exc())
            raise BringRequestException(
                "Authentication failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.debug("Exception: Cannot login:\n %s", traceback.format_exc())
            raise BringRequestException(
                "Authentication failed due to request exception."
            ) from e

        self.uuid = data["uuid"]
        self.public_uuid = data.get("publicUuid", "")
        self.headers["X-BRING-USER-UUID"] = self.uuid
        self.headers["Authorization"] = f'{data["token_type"]} {data["access_token"]}'
        self.refresh_token = data["refresh_token"]
        self.expires_in = data["expires_in"]

        locale = (await self.get_user_account())["userLocale"]
        self.headers["X-BRING-COUNTRY"] = locale["country"]
        self.user_locale = self.map_user_language_to_locale(locale)

        self.user_list_settings = await self.__load_user_list_settings()

        self.__translations = await self.__load_article_translations()

        return data

    async def load_lists(self) -> BringListResponse:
        """Load all shopping lists.

        Returns
        -------
        BringListResponse
            The JSON response.

        Raises
        ------
        BringRequestException
            If the request fails.
        BringParseException
            If the parsing of the request response fails.
        BringAuthException
            If the request fails due to invalid or expired authorization token.

        """
        try:
            url = f"{self.url}bringusers/{self.uuid}/lists"
            async with self._session.get(url, headers=self.headers) as r:
                _LOGGER.debug(
                    "Response from %s [%s]: %s", url, r.status, await r.text()
                )

                if r.status == HTTPStatus.UNAUTHORIZED:
                    try:
                        errmsg = await r.json()
                    except JSONDecodeError as e:
                        _LOGGER.debug(
                            "Exception: Cannot parse request response:\n %s",
                            traceback.format_exc(),
                        )
                        raise BringParseException(
                            "Loading lists failed due to authorization failure but "
                            "error response could not be parsed."
                        ) from e
                    _LOGGER.debug(
                        "Exception: Cannot get lists: %s",
                        errmsg["message"],
                    )
                    raise BringAuthException(
                        "Loading lists failed due to authorization failure, "
                        "the authorization token is invalid or expired."
                    )

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
                    _LOGGER.debug(
                        "Exception: Cannot get lists:\n %s", traceback.format_exc()
                    )
                    raise BringParseException(
                        "Loading lists failed during parsing of request response."
                    ) from e
        except asyncio.TimeoutError as e:
            _LOGGER.debug("Exception: Cannot get lists:\n %s", traceback.format_exc())
            raise BringRequestException(
                "Loading list failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.debug("Exception: Cannot get lists:\n %s", traceback.format_exc())
            raise BringRequestException(
                "Loading lists failed due to request exception."
            ) from e

    async def get_list(self, list_uuid: str) -> BringItemsResponse:
        """Get all items from a shopping list.

        Parameters
        ----------
        list_uuid : str
            A list uuid returned by load_lists()

        Returns
        -------
        BringItemsResponse
            The JSON response.

        Raises
        ------
        BringRequestException
            If the request fails.
        BringParseException
            If the parsing of the request response fails.
        BringAuthException
            If the request fails due to invalid or expired authorization token.

        """
        try:
            url = f"{self.url}v2/bringlists/{list_uuid}"
            async with self._session.get(url, headers=self.headers) as r:
                _LOGGER.debug(
                    "Response from %s [%s]: %s", url, r.status, await r.text()
                )

                if r.status == HTTPStatus.UNAUTHORIZED:
                    try:
                        errmsg = await r.json()
                    except JSONDecodeError as e:
                        _LOGGER.debug(
                            "Exception: Cannot parse request response:\n %s",
                            traceback.format_exc(),
                        )
                        raise BringParseException(
                            "Loading list items failed due to authorization failure but "
                            "error response could not be parsed."
                        ) from e
                    _LOGGER.debug(
                        "Exception: Cannot get list items: %s",
                        errmsg["message"],
                    )
                    raise BringAuthException(
                        "Loading list items failed due to authorization failure, "
                        "the authorization token is invalid or expired."
                    )

                r.raise_for_status()

                try:
                    data = await r.json()

                    for lst in data["items"].values():
                        for item in lst:
                            item["itemId"] = self.__translate(
                                item["itemId"],
                                to_locale=self.__locale(list_uuid),
                            )

                    return BringItemsResponse(
                        uuid=data["uuid"],
                        status=data["status"],
                        purchase=data["items"]["purchase"],
                        recently=data["items"]["recently"],
                    )
                except (JSONDecodeError, KeyError) as e:
                    _LOGGER.debug(
                        "Exception: Cannot get items for list %s:\n%s",
                        list_uuid,
                        traceback.format_exc(),
                    )
                    raise BringParseException(
                        "Loading list items failed during parsing of request response."
                    ) from e
        except asyncio.TimeoutError as e:
            _LOGGER.debug(
                "Exception: Cannot get items for list %s:\n%s",
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                "Loading list items failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.debug(
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
            A list uuid returned by load_lists()

        Returns
        -------
        BringListItemsDetailsResponse
            The JSON response. A list of item details.
            Caution: This is NOT a list of the items currently marked as 'to buy'.
            See get_list() for that.
            This contains the items that where customized by changing
            their default icon, category or uploading an image.

        Raises
        ------
        BringRequestException
            If the request fails.
        BringParseException
            If the parsing of the request response fails.
        BringAuthException
            If the request fails due to invalid or expired authorization token.

        """
        try:
            url = f"{self.url}bringlists/{list_uuid}/details"
            async with self._session.get(url, headers=self.headers) as r:
                _LOGGER.debug(
                    "Response from %s [%s]: %s", url, r.status, await r.text()
                )

                if r.status == HTTPStatus.UNAUTHORIZED:
                    try:
                        errmsg = await r.json()
                    except JSONDecodeError as e:
                        _LOGGER.debug(
                            "Exception: Cannot parse request response:\n %s",
                            traceback.format_exc(),
                        )
                        raise BringParseException(
                            "Loading list details failed due to authorization failure but "
                            "error response could not be parsed."
                        ) from e
                    _LOGGER.debug(
                        "Exception: Cannot get list details: %s",
                        errmsg["message"],
                    )
                    raise BringAuthException(
                        "Loading list details failed due to authorization failure, "
                        "the authorization token is invalid or expired."
                    )

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
                        for item in await r.json()
                    ]
                    return cast(BringListItemsDetailsResponse, data)
                except JSONDecodeError as e:
                    _LOGGER.debug(
                        "Exception: Cannot get item details for list %s:\n%s",
                        list_uuid,
                        traceback.format_exc(),
                    )
                    raise BringParseException(
                        "Loading list details failed during parsing of request response."
                    ) from e
        except asyncio.TimeoutError as e:
            _LOGGER.debug(
                "Exception: Cannot get item details for list %s:\n%s",
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                "Loading list details failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.debug(
                "Exception: Cannot get item details for list %s:\n%s",
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                "Loading list details failed due to request exception."
            ) from e

    async def save_item(
        self,
        list_uuid: str,
        item_name: str,
        specification: str = "",
        item_uuid: str = "",
    ) -> aiohttp.ClientResponse:
        """Save an item to a shopping list.

        Parameters
        ----------
        list_uuid : str
            A list uuid returned by load_lists()
        item_name : str
            The name of the item you want to save.
        specification : str, optional
            The details you want to add to the item.
        item_uuid : str, optional
            The uuid for the item to add. If a unique identifier is
            required it is recommended to generate a random uuid4.


        Returns
        -------
        Response
            The server response object.

        Raises
        ------
        BringRequestException
            If the request fails.

        """
        data = BringItem(
            itemId=item_name,
            spec=specification,
            uuid=item_uuid,
        )
        try:
            return await self.batch_update_list(list_uuid, data, BringItemOperation.ADD)
        except BringRequestException as e:
            _LOGGER.debug(
                "Exception: Cannot save item %s (%s) to list %s:\n%s",
                item_name,
                specification,
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                f"Saving item {item_name} ({specification}) to list {list_uuid} "
                "failed due to request exception."
            ) from e

    async def update_item(
        self,
        list_uuid: str,
        item_name: str,
        specification: str = "",
        item_uuid: str = "",
    ) -> aiohttp.ClientResponse:
        """Update an existing list item.

        Caution: Do not update `item_name`. Providing `item_uuid` makes it
        possible to update a specific item in case there are multiple
        items with the same name. If uuid is not specified, the newest
        item with the given `item_name` will be updated.

        Parameters
        ----------
        list_uuid : str
            A list uuid returned by load_lists()
        item_name : str
            The name of the item you want to update.
        specification : str, optional
            The details you want to update on the item.
        item_uuid : str, optional
            The uuid of the item to update.

        Returns
        -------
        Response
            The server response object.

        Raises
        ------
        BringRequestException
            If the request fails.

        """
        data = BringItem(
            itemId=item_name,
            spec=specification,
            uuid=item_uuid,
        )
        try:
            return await self.batch_update_list(list_uuid, data, BringItemOperation.ADD)
        except BringRequestException as e:
            _LOGGER.debug(
                "Exception: Cannot update item %s (%s) to list %s:\n%s",
                item_name,
                specification,
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                f"Updating item {item_name} ({specification}) in list {list_uuid} "
                "failed due to request exception."
            ) from e

    async def remove_item(
        self, list_uuid: str, item_name: str, item_uuid: str = ""
    ) -> aiohttp.ClientResponse:
        """Remove an item from a shopping list.

        Parameters
        ----------
        list_uuid : str
            A list uuid returned by load_lists()
        item_name : str
            The name of the item you want to remove.
        item_uuid : str, optional
            The uuid of the item you want to remove. The item to remove can be remove by only
            referencing its uuid and setting item_name to any nonempty string.

        Returns
        -------
        Response
            The server response object.

        Raises
        ------
        BringRequestException
            If the request fails.

        """
        data = BringItem(
            itemId=item_name,
            spec="",
            uuid=item_uuid,
        )
        try:
            return await self.batch_update_list(
                list_uuid, data, BringItemOperation.REMOVE
            )
        except BringRequestException as e:
            _LOGGER.debug(
                "Exception: Cannot delete item %s from list %s:\n%s",
                item_name,
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                f"Removing item {item_name} from list {list_uuid} "
                "failed due to request exception."
            ) from e

    async def complete_item(
        self,
        list_uuid: str,
        item_name: str,
        specification: str = "",
        item_uuid: str = "",
    ) -> aiohttp.ClientResponse:
        """Complete an item from a shopping list. This will add it to recent items.

        If it was not on the list, it will still be added to recent items.

        Parameters
        ----------
        list_uuid : str
            A list uuid returned by load_lists()
        item_name : str
            The name of the item you want to complete.
        specification : str, optional
            The details you want to update on the item.
        item_uuid : str, optional
            The uuid of the item you want to complete.

        Returns
        -------
        Response
            The server response object.

        Raises
        ------
        BringRequestException
            If the request fails.

        """
        data = BringItem(
            itemId=item_name,
            spec=specification,
            uuid=item_uuid,
        )
        try:
            return await self.batch_update_list(
                list_uuid, data, BringItemOperation.COMPLETE
            )
        except BringRequestException as e:
            _LOGGER.debug(
                "Exception: Cannot complete item %s in list %s:\n%s",
                item_name,
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                f"Completing item {item_name} from list {list_uuid} "
                "failed due to request exception."
            ) from e

    async def notify(
        self,
        list_uuid: str,
        notification_type: BringNotificationType,
        item_name: Optional[str] = None,
    ) -> aiohttp.ClientResponse:
        """Send a push notification to all other members of a shared list.

        Parameters
        ----------
        list_uuid : str
            A list uuid returned by loadLists()
        notification_type : BringNotificationType
            The type of notification to be sent
        item_name : str, optional
            The item_name **must** be included when notication_type
            is BringNotificationType.URGENT_MESSAGE

        Returns
        -------
        Response
            The server response object.

        Raises
        ------
        BringRequestException
            If the request fails.
        BringAuthException
            If the request fails due to invalid or expired authorization token.
        TypeError
            if the notification_type parameter is invalid.
        ValueError
            If the value for item_name is invalid.

        """
        json_data = BringNotificationsConfigType(
            arguments=[],
            listNotificationType=notification_type.value,
            senderPublicUserUuid=self.public_uuid,
        )

        if not isinstance(notification_type, BringNotificationType):
            _LOGGER.debug(
                "Exception: notificationType %s not supported. \n%s",
                notification_type,
                traceback.format_exc(),
            )
            raise TypeError(
                f"notificationType {notification_type} not supported,"
                "must be of type BringNotificationType."
            )
        if notification_type is BringNotificationType.URGENT_MESSAGE:
            if not item_name or len(item_name) == 0:
                _LOGGER.debug(
                    "Exception: Argument itemName missing:\n%s", traceback.format_exc()
                )
                raise ValueError(
                    "notificationType is URGENT_MESSAGE but argument itemName missing."
                )

            json_data["arguments"] = [item_name]
        try:
            url = f"{self.url}v2/bringnotifications/lists/{list_uuid}"
            async with self._session.post(
                url, headers=self.headers, json=json_data
            ) as r:
                _LOGGER.debug(
                    "Response from %s [%s]: %s", url, r.status, await r.text()
                )

                if r.status == HTTPStatus.UNAUTHORIZED:
                    try:
                        errmsg = await r.json()
                    except JSONDecodeError as e:
                        _LOGGER.debug(
                            "Exception: Cannot parse request response:\n %s",
                            traceback.format_exc(),
                        )
                        raise BringParseException(
                            "Sending notification failed due to authorization failure but "
                            "error response could not be parsed."
                        ) from e
                    _LOGGER.debug(
                        "Exception: Cannot send notification: %s",
                        errmsg["message"],
                    )
                    raise BringAuthException(
                        "Sending notification failed due to authorization failure, "
                        "the authorization token is invalid or expired."
                    )

                r.raise_for_status()
                return r
        except asyncio.TimeoutError as e:
            _LOGGER.debug(
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
            _LOGGER.debug(
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
                _LOGGER.debug(
                    "Response from %s [%s]: %s", url, r.status, await r.text()
                )

                if r.status == HTTPStatus.NOT_FOUND:
                    raise BringUserUnknownException(f"User {mail} does not exist.")

                r.raise_for_status()

        except asyncio.TimeoutError as e:
            _LOGGER.debug(
                "Exception: Cannot get verification for %s:\n%s",
                mail,
                traceback.format_exc(),
            )
            raise BringRequestException(
                "Verifying email failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            raise BringEMailInvalidException(f"E-mail {mail} is invalid.") from e

        return True

    def __load_article_translations_from_file(self, locale: str) -> dict[str, str]:
        """Read localization ressource files from disk.

        Parameters
        ----------
        locale : str
            A locale string

        Returns
        -------
            dict[str, str]:
                A translation table as a dict

        """
        dictionary_from_file: dict[str, str]

        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "locales",
            f"articles.{locale}.json",
        )
        with open(path, encoding="UTF-8") as f:
            dictionary_from_file = json.load(f)

        return dictionary_from_file

    async def __load_article_translations(self) -> dict[str, dict[str, str]]:
        """Load all required translation dictionaries into memory.

        Raises
        ------
        BringRequestException
            If the request fails.
        BringParseException
            If the parsing of the request response fails.

        Returns
        -------
        dict
            dict of downloaded dictionaries

        """
        dictionaries: dict[str, dict[str, str]] = {}

        locales_required = list(
            dict.fromkeys(
                [
                    list_setting.get("listArticleLanguage", self.user_locale)
                    for list_setting in self.user_list_settings.values()
                ]
                + [self.user_locale]
            )
        )

        for locale in locales_required:
            if locale == BRING_DEFAULT_LOCALE or locale not in BRING_SUPPORTED_LOCALES:
                continue

            try:
                dictionaries[locale] = await self.loop.run_in_executor(
                    None, self.__load_article_translations_from_file, locale
                )
                continue
            except OSError:
                _LOGGER.warning(
                    "Locale file articles.%s.json could not be loaded from filesystem. "
                    "Will continue trying to download locale.",
                    locale,
                )

            try:
                url = f"{LOCALES_BASE_URL}articles.{locale}.json"
                async with self._session.get(url) as r:
                    _LOGGER.debug("Response from %s [%s]", url, r.status)
                    r.raise_for_status()

                    try:
                        dictionaries[locale] = await r.json()
                    except JSONDecodeError as e:
                        _LOGGER.debug(
                            "Exception: Cannot load articles.%s.json:\n%s",
                            locale,
                            traceback.format_exc(),
                        )
                        raise BringParseException(
                            f"Loading article translations for locale {locale} "
                            "failed during parsing of request response."
                        ) from e
            except asyncio.TimeoutError as e:
                _LOGGER.debug(
                    "Exception: Cannot load articles.%s.json::\n%s",
                    locale,
                    traceback.format_exc(),
                )
                raise BringRequestException(
                    f"Loading article translations for locale {locale} "
                    "failed due to connection timeout."
                ) from e

            except aiohttp.ClientError as e:
                _LOGGER.debug(
                    "Exception: Cannot load articles.%s.json:\n%s",
                    locale,
                    traceback.format_exc(),
                )
                raise BringRequestException(
                    f"Loading article translations for locale {locale} "
                    "failed due to request exception."
                ) from e

        return dictionaries

    def __translate(
        self,
        item_id: str,
        *,
        to_locale: Optional[str] = None,
        from_locale: Optional[str] = None,
    ) -> str:
        """Translate a catalog item from or to a language.

        Parameters
        ----------
        item_id : str
            Item name.
        to_locale : str
            locale to translate to.
        from_locale : str
            locale to translate from.

        Returns
        -------
        str
            Translated Item name.

        Raises
        ------
        BringTranslationException
            If the translation fails.

        """

        locale = to_locale or from_locale

        if locale == BRING_DEFAULT_LOCALE:
            return item_id

        if not locale:
            raise ValueError("One of the arguments from_locale or to_locale required.")

        if locale not in BRING_SUPPORTED_LOCALES:
            _LOGGER.debug("Locale %s not supported by Bring.", locale)
            raise ValueError(f"Locale {locale} not supported by Bring.")
        try:
            return (
                self.__translations[locale].get(item_id, item_id)
                if to_locale
                else (
                    {value: key for key, value in self.__translations[locale].items()}
                ).get(item_id, item_id)
            )

        except Exception as e:
            _LOGGER.debug(
                "Exception: Cannot load translation dictionary:\n%s",
                traceback.format_exc(),
            )
            raise BringTranslationException(
                "Translation failed due to error loading translation dictionary."
            ) from e

    async def __load_user_list_settings(self) -> dict[str, dict[str, str]]:
        """Load user list settings into memory.

        Raises
        ------
        BringTranslationException
            If the user list settings could not be loaded.

        Returns
        -------
         dict[str, dict[str, str]]
            A dict of settings of the users lists

        """
        try:
            return {
                user_list_setting["listUuid"]: {
                    user_setting["key"]: user_setting["value"]
                    for user_setting in user_list_setting["usersettings"]
                }
                for user_list_setting in (await self.get_all_user_settings())[
                    "userlistsettings"
                ]
            }

        except Exception as e:
            _LOGGER.debug(
                "Exception: Cannot load user list settings:\n%s",
                traceback.format_exc(),
            )
            raise BringTranslationException(
                "Translation failed due to error loading user list settings."
            ) from e

    async def get_all_user_settings(self) -> BringUserSettingsResponse:
        """Load all user settings and user list settings.

        Returns
        -------
        BringUserSettingsResponse
            The JSON response.


        Raises
        ------
        BringRequestException
            If the request fails.
        BringParseException
            If the parsing of the request response fails.
        BringAuthException
            If the request fails due to invalid or expired authorization token.

        """
        try:
            url = f"{self.url}bringusersettings/{self.uuid}"
            async with self._session.get(url, headers=self.headers) as r:
                _LOGGER.debug(
                    "Response from %s [%s]: %s", url, r.status, await r.text()
                )

                if r.status == HTTPStatus.UNAUTHORIZED:
                    try:
                        errmsg = await r.json()
                    except JSONDecodeError as e:
                        _LOGGER.debug(
                            "Exception: Cannot parse request response:\n %s",
                            traceback.format_exc(),
                        )
                        raise BringParseException(
                            "Loading user settings failed due to authorization failure but "
                            "error response could not be parsed."
                        ) from e
                    _LOGGER.debug(
                        "Exception: Cannot get user settings: %s",
                        errmsg["message"],
                    )
                    raise BringAuthException(
                        "Loading user settings failed due to authorization failure, "
                        "the authorization token is invalid or expired."
                    )

                r.raise_for_status()

                try:
                    usersettings = [
                        cast(
                            BringUserSettingsEntry,
                            {
                                key: val
                                for key, val in item.items()
                                if key in BringUserSettingsEntry.__annotations__
                            },
                        )
                        for item in (await r.json())["usersettings"]
                    ]

                    userlistsettings = (await r.json())["userlistsettings"]
                    for i, listitem in enumerate(userlistsettings):
                        userlistsettings[i]["usersettings"] = [
                            cast(
                                BringUserSettingsEntry,
                                {
                                    key: val
                                    for key, val in item.items()
                                    if key in BringUserSettingsEntry.__annotations__
                                },
                            )
                            for item in listitem["usersettings"]
                        ]

                    userlistsettings = [
                        cast(
                            BringUserListSettingEntry,
                            {
                                key: val
                                for key, val in item.items()
                                if key in BringUserListSettingEntry.__annotations__
                            },
                        )
                        for item in userlistsettings
                    ]

                    data = cast(
                        BringUserSettingsResponse,
                        {
                            "usersettings": usersettings,
                            "userlistsettings": userlistsettings,
                        },
                    )

                    return data

                except JSONDecodeError as e:
                    _LOGGER.debug(
                        "Exception: Cannot get user settings for uuid %s:\n%s",
                        self.uuid,
                        traceback.format_exc(),
                    )
                    raise BringParseException(
                        "Loading user settings failed during parsing of request response."
                    ) from e
        except asyncio.TimeoutError as e:
            _LOGGER.debug(
                "Exception: Cannot get user settings for uuid %s:\n%s",
                self.uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                "Loading user settings failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.debug(
                "Exception: Cannot get user settings for uuid %s:\n%s",
                self.uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                "Loading user settings failed due to request exception."
            ) from e

    def __locale(self, list_uuid: str) -> str:
        """Get list or user locale.

        Returns
        -------
        str
            The locale from userlistsettings or user.

        Raises
        ------
        BringTranslationException
            If list locale could not be determined from the userlistsettings or user.

        """
        if list_uuid in self.user_list_settings:
            return self.user_list_settings[list_uuid].get(
                "listArticleLanguage", self.user_locale
            )
        return self.user_locale

    def map_user_language_to_locale(self, user_locale: dict[str, str]) -> str:
        """Map user language to a supported locale.

        The userLocale returned from the user account settings is not necessarily one of the 20
        locales used by the Bring App but rather what the user has set as language on their phone
        and the country where they are located. Usually the locale for the lists is always returned
        from the bringusersettings API endpoint. One exception exists, when user onboarding happens
        through the webApp, then the locale for the automatically created initial list is not set.
        For other lists this does not happen, as it is not possible to create more lists in the
        webApp, only in the mobile apps.

        Parameters
        ----------
        user_locale : dict
            user locale as a dict containing `language` and `country`.

        Returns
        -------
        str
            The locale corresponding to the users language.

        """
        locale = f'{user_locale["language"]}-{user_locale["country"]}'
        # if locale is a valid and supported locale we can use it.
        if locale in BRING_SUPPORTED_LOCALES:
            return locale

        # if language and country are not valid locales, we use only the language part and
        # map it to a corresponding locale or the most common for that language.
        return MAP_LANG_TO_LOCALE.get(user_locale["language"], BRING_DEFAULT_LOCALE)

    async def get_user_account(self) -> BringSyncCurrentUserResponse:
        """Get current user account.

        Returns
        -------
        BringSyncCurrentUserResponse
            The JSON response.


        Raises
        ------
        BringRequestException
            If the request fails.
        BringParseException
            If the parsing of the request response fails.
        BringAuthException
            If the request fails due to invalid or expired authorization token.

        """
        try:
            url = f"{self.url}v2/bringusers/{self.uuid}"
            async with self._session.get(url, headers=self.headers) as r:
                _LOGGER.debug(
                    "Response from %s [%s]: %s", url, r.status, await r.text()
                )

                if r.status == HTTPStatus.UNAUTHORIZED:
                    try:
                        errmsg = await r.json()
                    except JSONDecodeError as e:
                        _LOGGER.debug(
                            "Exception: Cannot parse request response:\n %s",
                            traceback.format_exc(),
                        )
                        raise BringParseException(
                            "Loading current user settings failed due to authorization failure but "
                            "error response could not be parsed."
                        ) from e
                    _LOGGER.debug(
                        "Exception: Cannot get current user settings: %s",
                        errmsg["message"],
                    )
                    raise BringAuthException(
                        "Loading current user settings failed due to authorization failure, "
                        "the authorization token is invalid or expired."
                    )

                r.raise_for_status()

                try:
                    data = cast(
                        BringSyncCurrentUserResponse,
                        {
                            key: val
                            for key, val in (await r.json()).items()
                            if key in BringSyncCurrentUserResponse.__annotations__
                        },
                    )
                    return data
                except JSONDecodeError as e:
                    _LOGGER.debug(
                        "Exception: Cannot get lists:\n %s", traceback.format_exc()
                    )
                    raise BringParseException(
                        "Loading lists failed during parsing of request response."
                    ) from e
        except asyncio.TimeoutError as e:
            _LOGGER.debug(
                "Exception: Cannot get current user settings:\n %s",
                traceback.format_exc(),
            )
            raise BringRequestException(
                "Loading current user settings failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.debug(
                "Exception: Cannot  current user settings:\n %s", traceback.format_exc()
            )
            raise BringRequestException(
                "Loading current user settings failed due to request exception."
            ) from e

    async def batch_update_list(
        self,
        list_uuid: str,
        items: BringItem | List[BringItem] | list[dict[str, str]],
        operation: Optional[BringItemOperation] = None,
    ) -> aiohttp.ClientResponse:
        """Batch update items on a shopping list.

        Parameters
        ----------
        list_uuid : str
            The listUuid of the list to make the changes to
        items : BringItem or List of BringItem
            Item(s) to add, complete or remove from the list
        operation : BringItemOperation, optional
            The Operation (ADD, COMPLETE, REMOVE) to perform for the supplied items on the list.
            Parameter can be ommited, and the BringItem key 'operation' can be set to TO_PURCHASE,
            TO_RECENTLY or REMOVE. Defaults to BringItemOperation.ADD if operation is neither
            passed as parameter nor is set in the BringItem.

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
            If the request fails due to invalid or expired authorization token.

        """
        if operation is None:
            operation = BringItemOperation.ADD

        _base_params = {
            "accuracy": "0.0",
            "altitude": "0.0",
            "latitude": "0.0",
            "longitude": "0.0",
        }
        if isinstance(items, dict):
            items = [items]
        json_data = {
            "changes": [
                {
                    **_base_params,
                    **item,
                    "itemId": self.__translate(
                        item["itemId"],
                        from_locale=self.__locale(list_uuid),
                    ),
                    "operation": str(item.get("operation", operation)),
                }
                for item in items
            ],
            "sender": "",
        }

        try:
            url = f"{self.url}v2/bringlists/{list_uuid}/items"
            async with self._session.put(
                url, headers=self.headers, json=json_data
            ) as r:
                _LOGGER.debug(
                    "Response from %s [%s]: %s", url, r.status, await r.text()
                )

                if r.status == HTTPStatus.UNAUTHORIZED:
                    try:
                        errmsg = await r.json()
                    except JSONDecodeError as e:
                        _LOGGER.debug(
                            "Exception: Cannot parse request response:\n %s",
                            traceback.format_exc(),
                        )
                        raise BringParseException(
                            "Batch operation failed due to authorization failure but "
                            "error response could not be parsed."
                        ) from e
                    _LOGGER.debug(
                        "Exception: Cannot get execute batch operation: %s",
                        errmsg["message"],
                    )
                    raise BringAuthException(
                        "Batch operation failed due to authorization failure, "
                        "the authorization token is invalid or expired."
                    )

                r.raise_for_status()
                return r
        except asyncio.TimeoutError as e:
            _LOGGER.debug(
                "Exception: Cannot execute batch operations for list %s:\n%s",
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                f"Batch operation for list {list_uuid} failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.debug(
                "Exception: Cannot execute batch operations for %s:\n%s",
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                f"Batch operation for list {list_uuid} failed due to request exception."
            ) from e

    async def retrieve_new_access_token(
        self, refresh_token: str | None = None
    ) -> BringAuthTokenRespone:
        """Refresh the access token.

        Parameters
        ----------
        refresh_token : str, optional
            The refresh token to use to retrieve a new access token

        Returns
        -------
        BringAuthTokenRespone
            The JSON response.

        Raises
        ------
        BringRequestException
            If the request fails.
        BringAuthException
            If the request fails due to invalid or expired refresh token.

        """
        refresh_token = refresh_token or self.refresh_token

        user_data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
        try:
            url = f"{self.url}v2/bringauth/token"
            async with self._session.post(
                url, headers=self.headers, data=user_data
            ) as r:
                _LOGGER.debug(
                    "Response from %s [%s]: %s",
                    url,
                    r.status,
                    await r.text()
                    if r.status != 200
                    else "",  # do not log response on success, as it contains sensible data
                )
                if r.status == HTTPStatus.UNAUTHORIZED:
                    try:
                        errmsg = await r.json()
                    except JSONDecodeError as e:
                        _LOGGER.debug(
                            "Exception: Cannot parse token request response:\n %s",
                            traceback.format_exc(),
                        )
                        raise BringParseException(
                            "Retrieve new access token failed due to authorization failure but "
                            "error response could not be parsed."
                        ) from e
                    _LOGGER.debug(
                        "Exception: Cannot retrieve new access token: %s",
                        errmsg["message"],
                    )
                    raise BringAuthException(
                        "Retrieve new access token failed due to authorization failure, "
                        "the refresh token is invalid or expired."
                    )

                r.raise_for_status()

                try:
                    data = cast(
                        BringAuthTokenRespone,
                        {
                            key: val
                            for key, val in (await r.json()).items()
                            if key in BringAuthTokenRespone.__annotations__
                        },
                    )
                except JSONDecodeError as e:
                    _LOGGER.debug(
                        "Exception: Cannot retrieve new access token:\n %s",
                        traceback.format_exc(),
                    )
                    raise BringParseException(
                        "Cannot parse token request response."
                    ) from e
        except asyncio.TimeoutError as e:
            _LOGGER.debug("Exception: Cannot login:\n %s", traceback.format_exc())
            raise BringRequestException(
                "Retrieve new access token failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.debug("Exception: Cannot login:\n %s", traceback.format_exc())
            raise BringRequestException(
                "Retrieve new access token failed due to request exception."
            ) from e

        self.headers["Authorization"] = f'{data["token_type"]} {data["access_token"]}'
        self.expires_in = data["expires_in"]

        return data

    async def set_list_article_language(
        self, list_uuid: str, language: str
    ) -> aiohttp.ClientResponse:
        """Set the article language for a specified list.

        Parameters
        ----------
        list_uuid : str
            The unique identifier for the list.
        language : str
            The language to set for the list articles.

        Returns
        -------
        aiohttp.ClientResponse
            The server response object.

        Raises
        ------
        ValueError
            If the specified language is not supported.
        BringRequestException
            If the request fails.
        BringAuthException
            If the request fails due to invalid or expired authorization token.

        """
        if language not in BRING_SUPPORTED_LOCALES:
            raise ValueError(f"Language {language} not supported.")

        url = f"{self.url}bringusersettings/{self.uuid}/{list_uuid}/listArticleLanguage"

        data = {"value": language}
        try:
            async with self._session.post(url, headers=self.headers, data=data) as r:
                _LOGGER.debug(
                    "Response from %s [%s]: %s", url, r.status, await r.text()
                )
                if r.status == HTTPStatus.UNAUTHORIZED:
                    raise BringAuthException(
                        "Set list article language failed due to authorization failure, "
                        "the authorization token is invalid or expired."
                    )
                r.raise_for_status()
                self.user_list_settings = await self.__load_user_list_settings()
                self.__translations = await self.__load_article_translations()
                return r
        except asyncio.TimeoutError as e:
            _LOGGER.debug(
                "Exception: Cannot set article language to %s for list %s:\n%s",
                language,
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                "Set list article language failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.debug(
                "Exception: Cannot set article language to %s for list %s:\n%s",
                language,
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                "Set list article language failed due to request exception."
            ) from e
