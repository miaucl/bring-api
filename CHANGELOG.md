# CHANGELOG

## 0.6.0

* **Pytest unit testing:** added pytest with full code coverage ([tr4nt0r](https://github.com/tr4nt0r))
* **Github workflow for pytest:** added workflow for running pytests with Python 3.11 & 3.12 on Ubuntu, Windows and macOS ([tr4nt0r](https://github.com/tr4nt0r))
* Update Python requirement to >=3.11
* Change from implicit to explicit string conversion of `BringItemOperation` in JSON request payload ([tr4nt0r](https://github.com/tr4nt0r))
* Change Type of `BringItemOperation` to `StrEnum` ([tr4nt0r](https://github.com/tr4nt0r))
* `BringItem::operation` now also accepts string literals `TO_PURCHASE`, `TO_RECENTLY` & `REMOVE` ([tr4nt0r](https://github.com/tr4nt0r))
* fix wrong variable name in `BringSyncCurrentUserResponse` class and add additional variables from JSON response ([tr4nt0r](https://github.com/tr4nt0r))
* Improve exceptions for `save/update/remove/complete_item` and `batch_update_list` methods ([tr4nt0r](https://github.com/tr4nt0r))
* Fix bug in `get_all_item_details` method ([tr4nt0r](https://github.com/tr4nt0r))
* Parsing error when parsing unauthorized response now raises `BringParseException` ([tr4nt0r](https://github.com/tr4nt0r))
* Cleanup legacy code ([tr4nt0r](https://github.com/tr4nt0r))

## 0.5.7

* **map user language to locales**: Bring sometimes stores non-standard locales in the user settings. In case the Bring API returns an invalid/unsupported locale, the user language is now mapped to a supported locale. 

## 0.5.6

* fix incorrect filtering of locales against supported locales list

## 0.5.5

* Fix KeyError when listArticleLanguage is not set.
  
## 0.5.4

* Load article translations from file in executor instead of event loop.

## 0.5.3

* Improve mypy type checking.
  
## 0.5.2

* Fixed build script to add locales explicitly.

## 0.5.1

* Add article translation tables to package. Translation tables are now loaded from file as data from web app is outdated.

## 0.5.0

* **New API method:** `batch_update_list`. Uses the same API endpoint as the mobile app to add, complete and remove items from shopping lists and has support for uuid as unique identifier for list items.  
* `save_item`, `update_item`, `complete_item` and `remove_item` are now wrapper methods for `batch_update_list` and have the additional parameter item_uuid.


## 0.4.1

* instead of downloading all translation tables, required locales are determined from the user list settings and the user locale. ([tr4nt0r](https://github.com/tr4nt0r))
* variable `userlistsettings` renamed to snake_cae `user_list_settings`. ([tr4nt0r](https://github.com/tr4nt0r))

## 0.4.0

* **Localization support:** catalog items are now automatically translated based on the shopping lists language if configured, otherwise the users default language is used ([tr4nt0r](https://github.com/tr4nt0r))
* **New API method:** `get_user_account`. Retrieves information about the current user like email, name and language ([tr4nt0r](https://github.com/tr4nt0r))
* **New API method:** `get_all_user_settings`. Retrieves user settings like default list and individual list settings for section order and language ([tr4nt0r](https://github.com/tr4nt0r))

## 0.3.1

* Unpin requirements and remove subdependencies ([tr4nt0r](https://github.com/tr4nt0r))

## 0.3.0

* Refactor for PEP8 compliance and code clean-up (breaking change) ([tr4nt0r](https://github.com/tr4nt0r))

## 0.2.0

* Add new method does_user_exist ([tr4nt0r](https://github.com/tr4nt0r))
* Fixes for test workflow

## 0.1.4

Add test workflow.

## 0.1.3

Add mypy for type-checking.

## 0.1.2

Add ruff as formatter and linter.

## 0.1.1

Change name of package to `bring-api`.

## 0.1.0

Test publish workflow for pypi, no code related changes.

## 0.0.1

Initial commit based on `3.0.0` from [eliasball](https://github.com/eliasball/python-bring-api).
