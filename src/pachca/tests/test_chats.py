import uuid
import logging
import time

import pytest

from pachca import Pachca
from pachca.exceptions import PachcaChatAlreadyExists

logger = logging.getLogger()


@pytest.mark.parametrize("channel,public", [
    (False, False),
    (False, True),
    (True, False),
    (True, True),
])
def test_create_chat(bot: Pachca, admin: Pachca, channel: bool, public: bool):
    """
    Test for `create message` method.

    Args:
        bot (Pachca): Pachca API client instance with bot access token.
        admin (Pachca): Pachca API client instance with admin access token.
        channel (bool): Is channel or discussion.
        public (bool): Is public.
    """

    name = str(uuid.uuid4())[:4]
    member_id = admin.get_user_id()

    created_chat = bot.create_chat(
        name=name,
        member_ids=[member_id],
        group_tag_ids=[],
        channel=channel,
        public=public,
        ignore_existing=True
    )

    received_chat = bot.get_chat(created_chat['id'])

    assert received_chat['name'] == name
    assert received_chat['channel'] == channel
    assert received_chat['public'] == public

    with pytest.raises(PachcaChatAlreadyExists):
        _ = bot.create_chat(
            name=name,
            member_ids=[member_id],
            group_tag_ids=[],
            channel=False,
            public=False,
            ignore_existing=False
        )

    time.sleep(1)
    admin.archive_chat(created_chat['id'])


@pytest.fixture(scope="function")
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

    time.sleep(3)
    admin.archive_chat(chat['id'])


@pytest.mark.parametrize("name,public", [
    ('abc', None),
    ('abc', True),
    ('abc', False),
    (None, True),
    (None, False),
])
def test_update_chat(bot, chat, name, public):
    """
    Test for `update chat` method.

    Args:
        bot (Pachca): Pachca API client instance with bot access token.
        chat (dict): Created chat dict.
        name (str): Name to change.
        public (bool): Public flag to change.
    """
    updated_chat = bot.update_chat(
        chat_id=chat['id'],
        name=name,
        public=public
    )
    if name is not None:
        assert updated_chat['name'] == name
    if public is not None:
        assert updated_chat['public'] == public


def test_archive_chat(admin: Pachca, chat: dict):
    """
    Test for `archive chat` method.

    Args:
        admin (Pachca): Pachca API client instance with admin access token.
        chat (dict): Created chat dict.
    """
    chat_id = chat['id']

    admin.archive_chat(chat_id)
    admin.unarchive_chat(chat_id)

    unarchived_chat = admin.get_chat(chat_id)
    assert unarchived_chat['id'] == chat_id