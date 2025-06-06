# Bring! Shopping Lists API

[![PyPI version](https://badge.fury.io/py/bring-api.svg)](https://pypi.org/p/bring-api)
[![Unit tests](https://github.com/miaucl/bring-api/actions/workflows/unit-tests.yaml/badge.svg)](https://github.com/miaucl/bring-api/actions/workflows/unit-tests.yaml)
[![Ruff](https://github.com/miaucl/bring-api/actions/workflows/ruff.yml/badge.svg)](https://github.com/miaucl/bring-api/actions/workflows/ruff.yml)
[![Mypy](https://github.com/miaucl/bring-api/actions/workflows/mypy.yaml/badge.svg)](https://github.com/miaucl/bring-api/actions/workflows/mypy.yaml)
[![Markdownlint](https://github.com/miaucl/bring-api/actions/workflows/markdownlint.yml/badge.svg)](https://github.com/miaucl/bring-api/actions/workflows/markdownlint.yml)
[![Docs](https://github.com/miaucl/bring-api/actions/workflows/documentation.yml/badge.svg)](https://github.com/miaucl/bring-api/actions/workflows/documentation.yml)
[![Smoke Test](https://github.com/miaucl/bring-api/actions/workflows/smoke-test.yaml/badge.svg)](https://github.com/miaucl/bring-api/actions/workflows/smoke-test.yaml)
[![codecov](https://codecov.io/gh/miaucl/bring-api/graph/badge.svg?token=BFGAENFT7M)](https://codecov.io/gh/miaucl/bring-api)

An unofficial python package to access the Bring! shopping lists API.

[![Sponsor](https://img.shields.io/badge/sponsor-30363D?style=for-the-badge&logo=GitHub-Sponsors&logoColor=#EA4AAA)](https://github.com/sponsors/miaucl)
[![BuyMeACoffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/miaucl)
[@miaucl](https://github.com/miaucl)

[![Sponsor](https://img.shields.io/badge/sponsor-30363D?style=for-the-badge&logo=GitHub-Sponsors&logoColor=#EA4AAA)](https://github.com/sponsors/tr4nt0r)
[![BuyMeACoffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/tr4nt0r)
[@tr4nt0r](https://github.com/tr4nt0r)

## Credits

> This implementation of the api is derived from the generic python implementation by [eliasball](https://github.com/eliasball/python-bring-api), which uses the legacy version of the api. This fork has been synced last time on 2024-02-11 and diverges from that point on using the non-legacy version. The implementation of [eliasball](https://github.com/eliasball/python-bring-api) is a **minimal** python port of the [node-bring-api](https://github.com/foxriver76/node-bring-api) by [foxriver76](https://github.com/foxriver76). All credit goes to him for making this awesome API possible!

## Disclaimer

The developers of this module are in no way endorsed by or affiliated with Bring! Labs AG, or any associated subsidiaries, logos or trademarks.

## Installation

As python package from [PyPI](https://pypi.org/p/bring-api)

`pip install bring-api`

Available as integration in [Home Assistant](https://www.home-assistant.io/integrations/bring/)

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=bring)

## Documentation

See below for usage examples. See [Exceptions](#exceptions) for API-specific exceptions and mitigation strategies for common exceptions.

## Usage Example

The API is based on the async HTTP library `aiohttp`.

```python
import aiohttp
import asyncio
import logging
import sys

from bring_api import Bring

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

async def main():
  async with aiohttp.ClientSession() as session:
    # Create Bring instance with email and password
    bring = Bring(session, "MAIL", "PASSWORD")
    # Login
    await bring.login()

    # Get information about all available shopping lists
    lists = (await bring.load_lists())["lists"]

    # Save an item with specifications to a certain shopping list
    await bring.save_item(lists[0]['listUuid'], 'Milk', 'low fat')

    # Save another item
    await bring.save_item(lists[0]['listUuid'], 'Carrots')

    # Get all the items of a list
    items = await bring.get_list(lists[0]['listUuid'])
    print(items)

    # Check off an item
    await bring.complete_item(lists[0]['listUuid'], 'Carrots')

    # Remove an item from a list
    await bring.remove_item(lists[0]['listUuid'], 'Milk')

asyncio.run(main())
```

## Manipulating lists with `batch_update_list`

This method uses the newer API endpoint for adding, completing and removing items from a list, which is also used in the Bring App. The items can be identified by their uuid and therefore some things are possible that are not possible with the legacy endpoints like:

- Add/complete/remove multiple items at once
- Adding multiple items with the same Name but different specifications
- You can work with a unique identifier for an item even before adding it to a list, just use uuid4 to generate a random uuid!

Usage examples:

### Add an item

When adding an item, the `itemId` is required, `spec` and `uuid` are optional. If you need a unique identifier before adding an item, you can just generate a uuid4.

```python
item = {
  "itemId": "Cilantro",
  "spec": "fresh",
  "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx"
}
await bring.batch_update_list(
  lists[0]['listUuid'],
  item,
  BringItemOperation.ADD)
```

### Updating an items specification

When updating an item, use ADD operation again. The `itemId` is required and the item `spec` will be added/updated on the existing item on the list. For better matching an existing item (if there is more than one item with the same `itemId`), you can use it's unique identifier `uuid`.

```python
item = {
  "itemId": "Cilantro",
  "spec": "dried",
  "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx"
}
await bring.batch_update_list(
  lists[0]['listUuid'],
  item,
  BringItemOperation.ADD)
```

### Multiple items

```python
# multiple items can be passed as list of items
items = [{
  "itemId": "Cilantro",
  "spec": "fresh",
  "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx"
},
{
  "itemId": "Parsley",
  "spec": "dried",
  "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx"
}]
await bring.batch_update_list(
  lists[0]['listUuid'],
  items,
  BringItemOperation.ADD)
```

### Add multiple items with the same name but different specifications

When adding items with the same name the parameter `uuid` is required, otherwise the previous item will be matched by `itemId` and it's specification will be overwritten

```python
items = [
  {
    "itemId": "Cilantro",
    "spec": "100g, dried",
    "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx"
  },
    {
    "itemId": "Cilantro",
    "spec": "fresh",
    "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx"
  }
]
await bring.batch_update_list(
  lists[0]['listUuid'],
  items,
  BringItemOperation.ADD)
```

### Removing or completing an item

When removing or completing an item you must submit `itemId` and `uuid`, `spec` is optional. Only the `uuid` will not work. Leaving out the `uuid` and submitting `itemId` and `spec` will also work. When submitting only `itemId` the Bring API will match the oldest item.

```python
await bring.batch_update_list(
  lists[0]['listUuid'],
  {"itemId": "Cilantro", "uuid" : "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx"},
  BringItemOperation.REMOVE)

await bring.batch_update_list(
  lists[0]['listUuid'],
  {"itemId": "Cilantro", "uuid" : "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx"},
  BringItemOperation.COMPLETE)  
```

### Renaming an item (not recommended)

An item that is already on the list can be renamed by sending it's `uuid` with a changed `itemId`. But it is highly advised against it because the Bring App will behave weirdly as it does not refresh an items name, not even when force reloading (going to the top of the list and pulling down). Users have to close the list by going to the overview or closing the app and only then when the list is completely refreshed the change of the name will show up.

```python
# Add an item
item = {
  "itemId": "Cilantro",
  "uuid" : "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx"
}
await bring.batch_update_list(
  lists[0]['listUuid'],
  item,
  BringItemOperation.ADD)

# Rename the item, and submit it again with the same uuid
item["itemId"] = "Coriander"
await bring.batch_update_list(
  lists[0]['listUuid'],
  item,
  BringItemOperation.ADD)  
```

## Exceptions

In case something goes wrong during a request, several exceptions can be thrown.
They will either be BringRequestException, BringParseException, or BringAuthException, depending on the context. All inherit from BringException.

### Another asyncio event loop is

With the async calls, you might encounter an error that another asyncio event loop is already running on the same thread. This is expected behavior according to the asyncio.run() [documentation](https://docs.python.org/3/library/asyncio-runner.html#asyncio.run). You cannot use more than one aiohttp session per thread, reuse the existing one!

### Exception ignored: RuntimeError: Event loop is closed

Due to a known issue in some versions of aiohttp when using Windows, you might encounter a similar error to this:

```python
Exception ignored in: <function _ProactorBasePipeTransport.__del__ at 0x00000000>
Traceback (most recent call last):
  File "C:\...\py38\lib\asyncio\proactor_events.py", line 116, in __del__
    self.close()
  File "C:\...\py38\lib\asyncio\proactor_events.py", line 108, in close
    self._loop.call_soon(self._call_connection_lost, None)
  File "C:\...\py38\lib\asyncio\base_events.py", line 719, in call_soon
    self._check_closed()
  File "C:\...\py38\lib\asyncio\base_events.py", line 508, in _check_closed
    raise RuntimeError('Event loop is closed')
RuntimeError: Event loop is closed
```

You can fix this according to [this](https://stackoverflow.com/questions/68123296/asyncio-throws-runtime-error-with-exception-ignored) stackoverflow answer by adding the following line of code before executing the library:

```python
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

## Dev

Setup the dev environment using VSCode, is is highly recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements_dev.txt
```

Install [pre-commit](https://pre-commit.com)

```bash
pre-commit install

# Run the commit hooks manually
pre-commit run --all-files
```

Following VSCode integrations may be helpful:

- [ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)
- [mypy](https://marketplace.visualstudio.com/items?itemName=matangover.mypy)
- [markdownlint](https://marketplace.visualstudio.com/items?itemName=DavidAnson.vscode-markdownlint)

### Releasing

A _final version_ can only be released from the `main` branch. To pass the gates of the `publish` workflow, the version must match in both the `tag` and `bring_api/__init__.py`.

To release a prerelease version, it must be done from a feature branch (**not** `main`). Prerelease versions are explicitly marked as such on the GitHub release page.
