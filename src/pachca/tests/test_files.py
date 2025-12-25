import os
import uuid
import logging
import time

import pytest

from pachca import Pachca
from pachca.file import File

logger = logging.getLogger()


@pytest.fixture(scope="module")
def chat(bot: Pachca, admin: Pachca):
    name = str(uuid.uuid4())[:4]
    chat = bot.create_chat(
        name=name,
        member_ids=[admin.get_user_id()],
        group_tag_ids=[],
        channel=False,
        public=False,
        ignore_existing=True
    )
    yield chat
    time.sleep(5)
    admin.archive_chat(chat['id'])


@pytest.fixture(scope="module")
def tmp_file_path():

    name = str(uuid.uuid4())[:4]
    ext = 'txt'
    path = f'/tmp/{name}.{ext}'

    with open(path, 'wt') as f:
        f.write('Test content.')
    yield path
    os.remove(path)


def test_upload_file(bot: Pachca, chat: dict, tmp_file_path: str):
    """
    Test for `upload file` method.

    Args:
        bot (Pachca): Pachca API client instance with bot access token.
        chat (dict): Created chat dict.
        tmp_file_path (str): Temporary file.

    Returns:
    """
    files = [
        File(file_path=tmp_file_path, file_type=File.FILE),
    ]

    created_message = bot.create_message(
        entity_id=chat['id'],
        entity_type='discussion',
        content='Message with file',
        files=files
    )
