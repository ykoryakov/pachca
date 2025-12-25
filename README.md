# Pachca

Simple Python API client for Pachca chat (https://pachca.com).

Official API reference: https://crm.pachca.com/dev/getting-started/overview/

```python
>>> from pachca import Pachca
>>> bot = Pachca(access_token='<token>')
>>> chat = bot.create_chat('Name')
>>> message = bot.create_message(chat_id=chat['id'], name='Hello!')
```

See full documentation at [Read the Docs](https://pachca.readthedocs.io)

## Installing Pachca

Pachca is available on PyPI:

```console
$ python -m pip install pachca
```

Pachca supports Python 3.9+.

## Supported Features

- Chat (create, get, update, find, archive, unarchive)
- Member (add, get, update, remove)
- Message (create, get, update, delete)
- Thread (create, get)

Not supported yet:

- Users 
- Reactions
- Buttons
- Export

## API Reference available on [Read the Docs](https://pachca.readthedocs.io)

[Read the Docs](https://pachca.readthedocs.io)

## Development and tests

To develop and run tests you need to:

- Prepare environment
- Register at [Pachca](https://pachca.com) and create new space
- Create test bot and copy `access_token`
- Create admin `access_token` and set permissions scope 
- Create `.env` file with `BOT_ACCESS_TOKEN` and `ADMIN_ACCESS_TOKEN`
- Run tests with `pytest` command

## Documentation

```console
cd ./docs
make html
```

Generated HTML documentation will be in `./docs/build/html`.
