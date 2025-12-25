import os
import logging

from dotenv import load_dotenv
import pytest

from pachca import Pachca

logger = logging.getLogger()


@pytest.fixture(scope="module")
def bot():
    load_dotenv()
    bot_access_token = os.getenv('BOT_ACCESS_TOKEN')

    with Pachca(access_token=bot_access_token) as bot:
        yield bot


@pytest.fixture(scope="module")
def admin():
    load_dotenv()
    admin_access_token = os.getenv('ADMIN_ACCESS_TOKEN')

    with Pachca(access_token=admin_access_token) as admin:
        yield admin
