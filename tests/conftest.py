"""Unit tests for bring-api."""

import aiohttp
from aioresponses import aioresponses
from dotenv import load_dotenv
import pytest

from bring_api.bring import Bring

load_dotenv()
UUID = "00000000-00000000-00000000-00000000"

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
    "userUuid": "{user_uuid}",
    "publicUserUuid": "{public_uuid}",
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


@pytest.fixture(name="session")
async def aiohttp_client_session():
    """Create  a client session."""
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture(name="bring")
async def bring_api_client(session):
    """Create Bring instance."""
    bring = Bring(session, "EMAIL", "PASSWORD")
    return bring


@pytest.fixture(name="mocked")
def aioclient_mock():
    """Mock Aiohttp client requests."""
    with aioresponses() as m:
        yield m
