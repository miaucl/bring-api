import asyncio
import logging
import traceback
from json import JSONDecodeError
from typing import List

import aiohttp

from .exceptions import BringAuthException, BringParseException, BringRequestException
from .types import (
    BringAuthResponse,
    BringItem,
    BringItemOperation,
    BringItemsResponse,
    BringListItemsDetailsResponse,
    BringListResponse,
    BringNotificationType,
)

_LOGGER = logging.getLogger(__name__)

class Bring:
    """
    Unofficial Bring API interface.
    """

    def __init__(self, session: aiohttp.ClientSession, mail: str, password: str) -> None:
        self._session = session

        self.mail = mail
        self.password = password
        self.uuid = ''
        self.publicUuid = ''

        self.url = 'https://api.getbring.com/rest/v2/'

        self.headers = {
            'Authorization': 'Bearer',
            'X-BRING-API-KEY': 'cof4Nc6D8saplXjE3h3HXqHH8m7VU2i1Gs0g85Sp',
            'X-BRING-CLIENT': 'android',
            'X-BRING-APPLICATION': 'bring',
            'X-BRING-COUNTRY': 'DE',
            'X-BRING-USER-UUID': ''
        }
        self.putHeaders = {
            'Authorization': '',
            'X-BRING-API-KEY': '',
            'X-BRING-CLIENT-SOURCE': '',
            'X-BRING-CLIENT': '',
            'X-BRING-COUNTRY': '',
            'X-BRING-USER-UUID': '',
            'Content-Type': ''
        }
        self.postHeaders = {
            'Authorization': '',
            'X-BRING-API-KEY': '',
            'X-BRING-CLIENT-SOURCE': '',
            'X-BRING-CLIENT': '',
            'X-BRING-COUNTRY': '',
            'X-BRING-USER-UUID': '',
            'Content-Type': ''
        }

    
    async def login(self) -> BringAuthResponse:
        """
        Try to login. 
        
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
        data = {
            'email': self.mail,
            'password': self.password
        }
        
        try:
            url = f'{self.url}bringauth'
            async with self._session.post(url, data=data) as r:
                _LOGGER.debug(f'Response from %s: %s', url, r.status)

                if r.status == 401:
                    try:
                        errmsg = await r.json()
                    except JSONDecodeError:
                        _LOGGER.error(f'Exception: Cannot parse login request response:\n{traceback.format_exc()}')
                    else:
                        _LOGGER.error(f'Exception: Cannot login: {errmsg["message"]}') 
                    raise BringAuthException('Login failed due to authorization failure, please check your email and password.')
                elif r.status == 400:
                    _LOGGER.error(f'Exception: Cannot login: {await r.text()}') 
                    raise BringAuthException('Login failed due to bad request, please check your email.')
                r.raise_for_status()

                try:
                    data = await r.json()
                except JSONDecodeError as e:
                    _LOGGER.error(f'Exception: Cannot login:\n{traceback.format_exc()}')
                    raise BringParseException(f'Cannot parse login request response.') from e
        except asyncio.TimeoutError as e:
            _LOGGER.error(f'Exception: Cannot login:\n{traceback.format_exc()}')
            raise BringRequestException('Authentication failed due to connection timeout.') from e
        except aiohttp.ClientError as e:
            _LOGGER.error(f'Exception: Cannot login:\n{traceback.format_exc()}')
            raise BringRequestException(f'Authentication failed due to request exception.') from e
        
        if 'uuid' not in data or 'access_token' not in data:
            _LOGGER.error('Exception: Cannot login: Data missing in API response.')
            raise BringAuthException('Login failed due to missing data in the API response, please check your email and password.')
        
        self.uuid = data['uuid']
        self.publicUuid = data.get('publicUuid', '')
        self.headers['X-BRING-USER-UUID'] = self.uuid
        self.headers['Authorization'] = f'Bearer {data["access_token"]}'
        self.putHeaders = {
            **self.headers,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        self.postHeaders = {
            **self.headers,
            'Content-Type': 'application/json; charset=UTF-8'
        }
        return data

    async def loadLists(self) -> BringListResponse:
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
            url = f'{self.url}bringusers/{self.uuid}/lists'
            async with self._session.get(url, headers=self.headers) as r:
                _LOGGER.debug(f'Response from %s: %s', url, r.status)
                r.raise_for_status()

                try: 
                    return await r.json()
                except JSONDecodeError as e:
                    _LOGGER.error(f'Exception: Cannot get lists:\n{traceback.format_exc()}')
                    raise BringParseException(f'Loading lists failed during parsing of request response.') from e
        except asyncio.TimeoutError as e:
            _LOGGER.error(f'Exception: Cannot get lists:\n{traceback.format_exc()}')
            raise BringRequestException('Loading list failed due to connection timeout.') from e
        except aiohttp.ClientError as e:
            _LOGGER.error(f'Exception: Cannot get lists:\n{traceback.format_exc()}')
            raise BringRequestException('Loading lists failed due to request exception.') from e

    async def getItems(self, listUuid: str) -> BringItemsResponse:
        """
        Get all items from a shopping list.

        Parameters
        ----------
        listUuid : str
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
            url = f'{self.url}bringlists/{listUuid}'
            async with self._session.get(url, headers=self.headers) as r:
                _LOGGER.debug(f'Response from %s: %s', url, r.status)
                r.raise_for_status()

                try:
                    return (await r.json())["items"]
                except JSONDecodeError as e:
                    _LOGGER.error(f'Exception: Cannot get items for list {listUuid}:\n{traceback.format_exc()}')
                    raise BringParseException('Loading list items failed during parsing of request response.') from e
        except asyncio.TimeoutError as e:
            _LOGGER.error(f'Exception: Cannot get items for list {listUuid}:\n{traceback.format_exc()}')
            raise BringRequestException('Loading list items failed due to connection timeout.') from e
        except aiohttp.ClientError as e:
            _LOGGER.error(f'Exception: Cannot get items for list {listUuid}:\n{traceback.format_exc()}')
            raise BringRequestException('Loading list items failed due to request exception.') from e


    async def getAllItemDetails(self, listUuid: str) -> BringListItemsDetailsResponse:
        """
        Get all details from a shopping list.

        Parameters
        ----------
        listUuid : str
            A list uuid returned by loadLists()

        Returns
        -------
        list
            The JSON response as a list. A list of item details.
            Caution: This is NOT a list of the items currently marked as 'to buy'. See getItems() for that.
        
        Raises
        ------
        BringRequestException
            If the request fails.
        BringParseException
            If the parsing of the request response fails.
        """
        try:
            url = f'{self.url}bringlists/{listUuid}/details'
            async with self._session.get(url, headers=self.headers) as r:
                _LOGGER.debug(f'Response from %s: %s', url, r.status)
                r.raise_for_status()

                try:
                    return await r.json()
                except JSONDecodeError as e:
                    _LOGGER.error(f'Exception: Cannot get item details for list {listUuid}:\n{traceback.format_exc()}')
                    raise BringParseException(f'Loading list details failed during parsing of request response.') from e
        except asyncio.TimeoutError as e:
            _LOGGER.error(f'Exception: Cannot get item details for list {listUuid}:\n{traceback.format_exc()}')
            raise BringRequestException('Loading list details failed due to connection timeout.') from e
        except aiohttp.ClientError as e:
            _LOGGER.error(f'Exception: Cannot get item details for list {listUuid}:\n{traceback.format_exc()}')
            raise BringRequestException('Loading list details failed due to request exception.') from e

    async def saveItem(self, listUuid: str, itemName: str, specification='') -> aiohttp.ClientResponse:
        """
        Save an item to a shopping list.

        Parameters
        ----------
        listUuid : str
            A list uuid returned by loadLists()
        itemName : str
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
            'purchase': itemName,
            'specification': specification,
        }
        try:
            url = f'{self.url}bringlists/{listUuid}'
            async with self._session.put(url, headers=self.putHeaders, data=data) as r:
                _LOGGER.debug(f'Response from %s: %s', url, r.status)
                r.raise_for_status()
                return r
        except asyncio.TimeoutError as e:
            _LOGGER.error(f'Exception: Cannot save item {itemName} ({specification}) to list {listUuid}:\n{traceback.format_exc()}')
            raise BringRequestException(f'Saving item {itemName} ({specification}) to list {listUuid} failed due to connection timeout.') from e
        except aiohttp.ClientError as e:
            _LOGGER.error(f'Exception: Cannot save item {itemName} ({specification}) to list {listUuid}:\n{traceback.format_exc()}')
            raise BringRequestException(f'Saving item {itemName} ({specification}) to list {listUuid} failed due to request exception.') from e

    async def updateItem(self, listUuid: str, itemName: str, specification='') -> aiohttp.ClientResponse:
        """
        Update an existing list item.

        Parameters
        ----------
        listUuid : str
            A list uuid returned by loadLists()
        itemName : str
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
            'purchase': itemName,
            'specification': specification
        }
        try:
            url = f'{self.url}bringlists/{listUuid}'
            async with self._session.put(url, headers=self.putHeaders, data=data) as r:
                _LOGGER.debug(f'Response from %s: %s', url, r.status)
                r.raise_for_status()
                return r
        except asyncio.TimeoutError as e:
            _LOGGER.error(f'Exception: Cannot update item {itemName} ({specification}) to list {listUuid}:\n{traceback.format_exc()}')
            raise BringRequestException(f'Updating item {itemName} ({specification}) in list {listUuid} failed due to connection timeout.') from e
        except aiohttp.ClientError as e:
            _LOGGER.error(f'Exception: Cannot update item {itemName} ({specification}) to list {listUuid}:\n{traceback.format_exc()}')
            raise BringRequestException(f'Updating item {itemName} ({specification}) in list {listUuid} failed due to request exception.') from e
 
    async def removeItem(self, listUuid: str, itemName: str) -> aiohttp.ClientResponse:
        """
        Remove an item from a shopping list.

        Parameters
        ----------
        listUuid : str
            A list uuid returned by loadLists()
        itemName : str
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
            'remove': itemName,
        }
        try:
            url = f'{self.url}bringlists/{listUuid}'
            async with self._session.put(url, headers=self.putHeaders, data=data) as r:
                _LOGGER.debug(f'Response from %s: %s', url, r.status)
                r.raise_for_status()
                return r
        except asyncio.TimeoutError as e:
            _LOGGER.error(f'Exception: Cannot remove item {itemName} to list {listUuid}:\n{traceback.format_exc()}')
            raise BringRequestException(f'Removing item {itemName} from list {listUuid} failed due to connection timeout.') from e
        except aiohttp.ClientError as e:
            _LOGGER.error(f'Exception: Cannot remove item {itemName} to list {listUuid}:\n{traceback.format_exc()}')
            raise BringRequestException(f'Removing item {itemName} from list {listUuid} failed due to request exception.') from e

    async def completeItem(self, listUuid: str, itemName: str) -> aiohttp.ClientResponse:
        """
        Complete an item from a shopping list. This will add it to recent items.
        If it was not on the list, it will still be added to recent items.

        Parameters
        ----------
        listUuid : str
            A list uuid returned by loadLists()
        itemName : str
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
            'recently': itemName
        }
        try:
            url = f'{self.url}bringlists/{listUuid}'
            async with self._session.put(url, headers=self.putHeaders, data=data) as r:
                _LOGGER.debug(f'Response from %s: %s', url, r.status)
                r.raise_for_status()
                return r
        except asyncio.TimeoutError as e:
            _LOGGER.error(f'Exception: Cannot complete item {itemName} to list {listUuid}:\n{traceback.format_exc()}')
            raise BringRequestException(f'Completing item {itemName} from list {listUuid} failed due to connection timeout.') from e
        except aiohttp.ClientError as e:
            _LOGGER.error(f'Exception: Cannot complete item {itemName} to list {listUuid}:\n{traceback.format_exc()}')
            raise BringRequestException(f'Completing item {itemName} from list {listUuid} failed due to request exception.') from e
    
    async def notify(self, listUuid: str, notificationType: BringNotificationType, itemName: str = None) -> aiohttp.ClientResponse:
        """
        Send a push notification to all other members of a shared list.

        Parameters
        ----------
        listUuid : str
            A list uuid returned by loadLists()
        notificationType : BringNotificationType
        itemName : str, optional
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
        json = {
            'arguments': [],
            'listNotificationType': notificationType.value,
            'senderPublicUserUuid': self.publicUuid
        }

        if not isinstance(notificationType, BringNotificationType):
            _LOGGER.error(f'Exception: notificationType {notificationType} not supported.')
            raise ValueError(f'notificationType {notificationType} not supported, must be of type BringNotificationType.')
        if notificationType is BringNotificationType.URGENT_MESSAGE:
            if not itemName or len(itemName) == 0 :
                _LOGGER.error('Exception: Argument itemName missing.')
                raise ValueError('notificationType is URGENT_MESSAGE but argument itemName missing.')
            else:
                json['arguments'] = [itemName]
        try:
            url = f'{self.url}bringnotifications/lists/{listUuid}'
            async with self._session.post(url, headers=self.postHeaders, json=json) as r:
                _LOGGER.debug(f'Response from %s: %s', url, r.status)
                r.raise_for_status()
                return r
        except asyncio.TimeoutError as e:
            _LOGGER.error(f'Exception: Cannot send notification {notificationType} for list {listUuid}:\n{traceback.format_exc()}')
            raise BringRequestException(f'Sending notification {notificationType} for list {listUuid} failed due to connection timeout.') from e
        except aiohttp.ClientError as e:
            _LOGGER.error(f'Exception: Cannot send notification {notificationType} for list {listUuid}:\n{traceback.format_exc()}')
            raise BringRequestException(f'Sending notification {notificationType} for list {listUuid} failed due to request exception.') from e


    async def change_list(
        self,
        list_uuid: str,
        items: BringItem | List[BringItem],
        operation: BringItemOperation = BringItemOperation.ADD
    ) -> aiohttp.ClientResponse:
        """
        Batch update items on a shopping list.
        
        Parameters
        ----------
        list_uuid : str
            The listUuid of the list to make the changes to 
        items : BringItem or List of BringItem
            Item(s) to add, complete or remove from the list
        operation : BringItemOperation
            The Operation (ADD, COMPLETE, REMOVE) to perform for the supplied items on the list

        Returns
        -------
        Response
            The server response object.

        Raises
        ------
        BringRequestException
            If the request fails.
        """
        _base_params = {
            "accuracy": "0.0",
            "altitude": "0.0",
            "itemId": "",
            "latitude": "0.0",
            "longitude": "0.0",
            "operation": "",
            "spec": "",
            "uuid": "",
        }

        json = {
            "changes": [],
            "sender": "",
        }

        if isinstance(items, dict):
            items = [items]
        for item in items:
            json["changes"].append( {
                **_base_params,
                **item,
                "operation": operation.value
            })

        try:
            url = f"{self.url}bringlists/{list_uuid}/items"
            async with self._session.put(
                url, headers=self.headers, json=json
            ) as r:
                _LOGGER.debug("Response from %s: %s", url, r.status)
                r.raise_for_status()
                return r
        except asyncio.TimeoutError as e:
            _LOGGER.error(
                "Exception: Cannot execute batch operation %s for list %s:\n%s",
                operation.name,
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                f"Operation {operation.name} for list {list_uuid} failed due to connection timeout."
            ) from e
        except aiohttp.ClientError as e:
            _LOGGER.error(
                "Exception: Cannot execute batch operations for %s:\n%s",
                list_uuid,
                traceback.format_exc(),
            )
            raise BringRequestException(
                f"Operation {operation.name} for list {list_uuid} failed due to request exception."
            ) from e
