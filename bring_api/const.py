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
    "de-AT",
    "de-CH",
    "de-DE",
    "en-AU",
    "en-CA",
    "en-GB",
    "en-US",
    "es-ES",
    "fr-CH",
    "fr-FR",
    "hu-HU",
    "it-CH",
    "it-IT",
    "nb-NO",
    "nl-NL",
    "pl-PL",
    "pt-BR",
    "ru-RU",
    "sv-SE",
    "tr-TR",
]

MAP_LANG_TO_LOCALE = {
    "de": "de-DE",
    "en": "en-US",
    "es": "es-ES",
    "fr": "fr-FR",
    "hu": "hu-HU",
    "it": "it-IT",
    "nb": "nb-NO",
    "nl": "nl-NL",
    "pl": "pl-PL",
    "pt": "pt-BR",
    "ru": "ru-RU",
    "sv": "sv-SE",
    "tr": "tr-TR",
}

BRING_DEFAULT_LOCALE: Final = "de-CH"
