"""Constants for bring-api."""
from typing import Final

API_BASE_URL: Final = "https://api.getbring.com/rest/"
DEFAULT_HEADERS: Final = {
    "Authorization": "Bearer",
    "X-BRING-API-KEY": "cof4Nc6D8saplXjE3h3HXqHH8m7VU2i1Gs0g85Sp",
    "X-BRING-CLIENT": "android",
    "X-BRING-APPLICATION": "bring",
    "X-BRING-COUNTRY": "DE",
    "X-BRING-USER-UUID": "",
}

LOCALES_BASE_URL: Final = "https://web.getbring.com/locale/"
BRING_SUPPORTED_LOCALES: Final = [
    "en-AU",
    "de-DE",
    "fr-FR",
    "it-IT",
    "en-CA",
    "nl-NL",
    "nb-NO",
    "pl-PL",
    "pt-BR",
    "ru-RU",
    "sv-SE",
    "de-CH",
    "fr-CH",
    "it-CH",
    "es-ES",
    "tr-TR",
    "en-GB",
    "en-US",
    "hu-HU",
    "de-AT",
]

BRING_DEFAULT_LOCALE: Final = "de-CH"
