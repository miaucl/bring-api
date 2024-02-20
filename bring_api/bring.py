"""Bring api implementation."""
import asyncio
from json import JSONDecodeError
import logging
import traceback
from typing import Any, Optional, cast

import aiohttp

from .const import (
    API_BASE_URL,
    BRING_DEFAULT_LOCALE,
    BRING_SUPPORTED_LOCALES,
    DEFAULT_HEADERS,
    LOCALES_BASE_URL,
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
        self.userlistsettings: dict[str, dict[str, str]] = {}
        self.user_locale = BRING_DEFAULT_LOCALE

        self.__translations: dict[str, dict[str, str]] = {}
        self.uuid = ""

        self.url = API_BASE_URL

        self.headers = DEFAULT_HEADERS

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

        locale = (await self.get_user_account())["userLocale"]
        self.headers["X-BRING-COUNTRY"] = locale["country"]
        self.user_locale = f'{locale["language"]}-{locale["country"]}'

        if len(self.__translations) == 0:
            await self.__load_article_translations()

        if len(self.userlistsettings) == 0:
            await self.__load_user_list_settings()

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

                    for lst in data.values():
                        for item in cast(dict[Any, Any], lst):
                            item["itemId"] = self.__translate(
                                item["itemId"],
                                to_locale=self.__locale(list_uuid),
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
            "purchase": self.__translate(
                item_name,
                from_locale=self.__locale(list_uuid),
            ),
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
        data = {
            "purchase": self.__translate(
                item_name,
                from_locale=self.__locale(list_uuid),
            ),
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
            "remove": self.__translate(
                item_name,
                from_locale=self.__locale(list_uuid),
            ),
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
        data = {
            "recently": self.__translate(
                item_name,
                from_locale=self.__locale(list_uuid),
            )
        }
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

    async def __load_article_translations(self) -> None:
        """Load all translation dictionaries into memory.

        Raises
        ------
        BringRequestException
            If the request fails.

        """

        for locale in BRING_SUPPORTED_LOCALES:
            try:
                url = f"{LOCALES_BASE_URL}articles.{locale}.json"
                async with self._session.get(url) as r:
                    _LOGGER.debug("Response from %s: %s", url, r.status)
                    r.raise_for_status()

                    try:
                        self.__translations[locale] = await r.json()
                    except JSONDecodeError as e:
                        _LOGGER.error(
                            "Exception: Cannot load articles.%s.json:\n%s",
                            locale,
                            traceback.format_exc(),
                        )
                        raise BringParseException(
                            f"Loading article translations for locale {locale}"
                            "failed during parsing of request response."
                        ) from e
            except asyncio.TimeoutError as e:
                _LOGGER.error(
                    "Exception: Cannot load articles.%s.json::\n%s",
                    locale,
                    traceback.format_exc(),
                )
                raise BringRequestException(
                    f"Loading article translations for locale {locale}"
                    "failed due to connection timeout."
                ) from e

            except aiohttp.ClientError as e:
                _LOGGER.error(
                    "Exception: Cannot load articles.%s.json:\n%s",
                    locale,
                    traceback.format_exc(),
                )
                raise BringRequestException(
                    f"Loading article translations for locale {locale}"
                    "failed due to request exception."
                ) from e

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
            _LOGGER.error(
                "Exception: Cannot load translation dictionary:\n%s",
                traceback.format_exc(),
            )
            raise BringTranslationException(
                "Translation failed due to error loading translation dictionary."
            ) from e

    async def __load_user_list_settings(self) -> None:
        """Load user list settings into memory.

        Raises
        ------
        BringTranslationException
            If the userlistsettings coould not be loaded.

        """
        try:
            self.userlistsettings = {
                user_list_setting["listUuid"]: {
                    user_setting["key"]: user_setting["value"]
                    for user_setting in user_list_setting["usersettings"]
                }
                for user_list_setting in (await self.get_all_user_settings())[
                    "userlistsettings"
                ]
            }
        except Exception as e:
            _LOGGER.error(
                "Exception: Cannot load userlistsettings:\n%s",
                traceback.format_exc(),
            )
            raise BringTranslationException(
                "Translation failed due to error loading userlistsettings."
            ) from e

    async def get_all_user_settings(self) -> BringUserSettingsResponse:
        """Load all user settings and user list settings.

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
            url = f"{self.url}bringusersettings/{self.uuid}"
            async with self._session.get(url, headers=self.headers) as r:
                _LOGGER.debug("Response from %s: %s", url, r.status)
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
                    _LOGGER.error(
                        "Exception: Cannot get user settings for uuid %s:\n%s",
                        self.uuid,
                        traceback.format_exc(),
                    )
                    raise BringParseException(
                        "Loading user settings failed during parsing of request response."
                    ) from e
        except asyncio.TimeoutError as e:
            _LOGGER.error(
                "Exception: Cannot get user settings for uuid %s:\n%s",
                self.uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                "Loading user settings failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.error(
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
        if list_uuid in self.userlistsettings:
            return self.userlistsettings[list_uuid]["listArticleLanguage"]
        return self.user_locale

    async def get_user_account(self) -> BringSyncCurrentUserResponse:
        """Get current user account.

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
            url = f"{self.url}v2/bringusers/{self.uuid}"
            async with self._session.get(url, headers=self.headers) as r:
                _LOGGER.debug("Response from %s: %s", url, r.status)
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
                    _LOGGER.error(
                        "Exception: Cannot get lists:\n %s", traceback.format_exc()
                    )
                    raise BringParseException(
                        "Loading lists failed during parsing of request response."
                    ) from e
        except asyncio.TimeoutError as e:
            _LOGGER.error(
                "Exception: Cannot get current user settings:\n %s",
                traceback.format_exc(),
            )
            raise BringRequestException(
                "Loading current user settings failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.error(
                "Exception: Cannot  current user settings:\n %s", traceback.format_exc()
            )
            raise BringRequestException(
                "Loading current user settings failed due to request exception."
            ) from e
