# Bring! Shopping Lists API

[![PyPI version](https://badge.fury.io/py/bring-api.svg)](https://badge.fury.io/py/bring-api)

An unofficial python package to access the Bring! shopping lists API.

## Credits

> This implementation of the api is derived from the generic python implementation by [eliasball](https://github.com/eliasball/python-bring-api), which uses the legacy version of the api. This fork has been synced last time on 2024-02-11 and diverges from that point on using the non-legacy version. The implementation of [eliasball](https://github.com/eliasball/python-bring-api) is a **minimal** python port of the [node-bring-api](https://github.com/foxriver76/node-bring-api) by [foxriver76](https://github.com/foxriver76). All credit goes to him for making this awesome API possible!

## Disclaimer

The developers of this module are in no way endorsed by or affiliated with Bring! Labs AG, or any associated subsidiaries, logos or trademarks.

## Installation

`pip install bring-api`

## Documentation

See below for usage examples. See [Exceptions](#exceptions) for API-specific exceptions and mitigation strategies for common exceptions.

## Usage Example

The API is based on the async HTTP library `aiohttp`.

```python
import aiohttp
import asyncio
import logging
import sys

from bring_api.bring import Bring

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

## Exceptions

In case something goes wrong during a request, several exceptions can be thrown.
They will either be BringRequestException, BringParseException, or BringAuthException, depending on the context. All inherit from BringException.

### Another asyncio event loop is already running

Because even the sync methods use async calls under the hood, you might encounter an error that another asyncio event loop is already running on the same thread. This is expected behavior according to the asyncio.run() [documentation](https://docs.python.org/3/library/asyncio-runner.html#asyncio.run). You cannot call the sync methods when another event loop is already running. When you are already inside an async function, you should use the async methods instead.

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

# Run tests locally (using a .env file is supported and recommended)
export EMAIL=...
export PASSWORD=...
export LIST=...
python test.py
```

Following VSCode integrations may be helpful:

* [ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)
* [mypy](https://marketplace.visualstudio.com/items?itemName=matangover.mypy)
