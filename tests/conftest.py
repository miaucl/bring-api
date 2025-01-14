"""Unit tests for bring-api."""

import aiohttp
from aioresponses import aioresponses
from dotenv import load_dotenv
import pytest

from bring_api.bring import Bring

load_dotenv()
UUID = "00000000-0000-0000-0000-000000000000"

BRING_LOGIN_RESPONSE = {
    "uuid": UUID,
    "publicUuid": UUID,
    "email": "EMAIL",
    "name": "NAME",
    "photoPath": "",
    "bringListUUID": UUID,
    "access_token": "ACCESS_TOKEN",
    "refresh_token": "REFRESH_TOKEN",
    "token_type": "Bearer",
    "expires_in": 604799,
}

BRING_USER_ACCOUNT_RESPONSE = {
    "userUuid": "00000000-0000-0000-0000-000000000000",
    "publicUserUuid": "00000000-0000-0000-0000-000000000000",
    "email": "{email}",
    "emailVerified": True,
    "name": "{user_name}",
    "photoPath": "bring/user/portrait/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx",
    "userLocale": {"language": "de", "country": "DE"},
    "premiumConfiguration": {
        "hasPremium": False,
        "hideSponsoredProducts": False,
        "hideSponsoredTemplates": False,
        "hideSponsoredPosts": False,
        "hideSponsoredCategories": False,
        "hideOffersOnMain": False,
    },
}

BRING_USER_SETTINGS_RESPONSE = {
    "usersettings": [
        {"key": "autoPush", "value": "ON"},
        {"key": "purchaseStyle", "value": "grouped"},
        {"key": "premiumHideSponsoredCategories", "value": "OFF"},
        {"key": "premiumHideInspirationsBadge", "value": "OFF"},
        {"key": "premiumHideOffersBadge", "value": "OFF"},
        {"key": "premiumHideOffersOnMain", "value": "OFF"},
        {"key": "defaultListUUID", "value": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx"},
        {"key": "discountActivatorOnMainEnabled", "value": "OFF"},
        {"key": "onboardClient", "value": "android"},
    ],
    "userlistsettings": [
        {
            "listUuid": UUID,
            "usersettings": [
                {
                    "key": "listSectionOrder",
                    "value": '["Früchte & Gemüse","Brot & Gebäck","Milch & Käse","Fleisch & Fisch","Zutaten & Gewürze","Fertig- & Tiefkühlprodukte","Getreideprodukte","Snacks & Süsswaren","Getränke & Tabak","Haushalt & Gesundheit","Pflege & Gesundheit","Tierbedarf","Baumarkt & Garten","Eigene Artikel"]',
                },
                {"key": "listArticleLanguage", "value": "de-DE"},
            ],
        }
    ],
}

BRING_LOAD_LISTS_RESPONSE = {
    "lists": [
        {
            "listUuid": UUID,
            "name": "Einkauf",
            "theme": "ch.publisheria.bring.theme.home",
        },
    ]
}

BRING_GET_LIST_RESPONSE = {
    "uuid": UUID,
    "status": "SHARED",
    "items": {
        "purchase": [
            {
                "uuid": "43bdd5a2-740a-4230-8b27-d0bbde886da7",
                "specification": "grün",
                "itemId": "Paprika",
            },
            {
                "uuid": "2de9d1c0-c211-4129-b6c5-c1260c3fc735",
                "specification": "gelb",
                "itemId": "Zucchetti",
            },
        ],
        "recently": [
            {
                "uuid": "5681ed79-c8e4-4c8b-95ec-112999d016c0",
                "specification": "rot",
                "itemId": "Paprika",
            },
            {
                "uuid": "01eea2cd-f433-4263-ad08-3d71317c4298",
                "specification": "",
                "itemId": "Pouletbrüstli",
            },
        ],
    },
}

BRING_GET_ALL_ITEM_DETAILS_RESPONSE = [
    {
        "uuid": "bfb5634c-d219-4d66-b68e-1388e54f0bb0",
        "itemId": "Milchreis",
        "listUuid": UUID,
        "userIconItemId": "Reis",
        "userSectionId": "Getreideprodukte",
        "assignedTo": "",
        "imageUrl": "",
    },
    {
        "uuid": "0056b23c-7fc3-44da-8c34-426f8b632220",
        "itemId": "Zitronensaft",
        "listUuid": UUID,
        "userIconItemId": "Zitrone",
        "userSectionId": "Zutaten & Gewürze",
        "assignedTo": "",
        "imageUrl": "",
    },
]

BRING_TOKEN_RESPONSE = {
    "access_token": "{access_token}",
    "refresh_token": "{refresh_token}",
    "token_type": "Bearer",
    "expires_in": 604799,
}

BRING_GET_ACTIVITY_RESPONSE = {
    "timeline": [
        {
            "type": "LIST_ITEMS_CHANGED",
            "content": {
                "uuid": "673594a9-f92d-4cb6-adf1-d2f7a83207a4",
                "purchase": [
                    {
                        "uuid": "658a3770-1a03-4ee0-94a6-10362a642377",
                        "itemId": "Gurke",
                        "specification": "",
                        "attributes": [],
                    }
                ],
                "recently": [
                    {
                        "uuid": "1ed22d3d-f19b-4530-a518-19872da3fd3e",
                        "itemId": "Milch",
                        "specification": "",
                        "attributes": [],
                    }
                ],
                "sessionDate": "2025-01-01T03:09:33.036Z",
                "publicUserUuid": "98615d7e-0a7d-4a7e-8f73-a9cbb9f1bc32",
            },
        },
        {
            "type": "LIST_ITEMS_ADDED",
            "content": {
                "uuid": "9a16635c-dea2-4e00-904a-c5034f9cfecf",
                "items": [
                    {
                        "uuid": "66a633a2-ae09-47bf-8845-3c0198480544",
                        "itemId": "Joghurt",
                        "specification": "",
                        "attributes": [],
                    },
                ],
                "sessionDate": "2025-01-01T02:54:57.656Z",
                "publicUserUuid": "6743a171-247d-46d0-bc06-baf31194f949",
            },
        },
        {
            "type": "LIST_ITEMS_REMOVED",
            "content": {
                "uuid": "303dedf6-d4b2-4d25-a8cd-1c7967b84fcb",
                "items": [
                    {
                        "uuid": "2ba8ddb6-01c6-4b0b-a89d-f3da6b291528",
                        "itemId": "Tofu",
                        "specification": "",
                        "attributes": [],
                    }
                ],
                "sessionDate": "2025-01-01T03:09:12.380Z",
                "publicUserUuid": "6d79d10b-70b2-443f-9f7e-0b02e670c402",
            },
        },
    ],
    "timestamp": "2025-01-01T03:09:33.036Z",
    "totalEvents": 2,
}

BRING_ERROR_RESPONSE = {
    "message": "",
    "error": "",
    "error_description": "",
    "errorcode": 0,
}


@pytest.fixture(name="headers")
async def headers() -> str:
    """Load the headers."""

    # Open and read the file
    with open("tests/test.headers", encoding="utf-8") as file:
        return file.read()


@pytest.fixture(name="session")
async def aiohttp_client_session():
    """Create  a client session."""
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture(name="bring")
async def bring_api_client(session) -> Bring:
    """Create Bring instance."""
    bring = Bring(session, "EMAIL", "PASSWORD")
    return bring


@pytest.fixture(name="mocked")
def aioclient_mock():
    """Mock Aiohttp client requests."""
    with aioresponses() as m:
        yield m
