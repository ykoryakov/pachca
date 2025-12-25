import uuid
import logging
import time

import pytest

from pachca import Pachca

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


content_wo_link = """
Lorem Ipsum is a type of placeholder text commonly used in the design and publishing industries to fill a space on a page and give an impression of how the final content will look. It is derived from a Latin text by the Roman philosopher Cicero and has been used since the 1960s. The text is nonsensical and does not convey any specific meaning, allowing designers to focus on layout and visual elements without the distraction of meaningful content.
"""

content_w_link = """
Lorem Ipsum is a type of placeholder text commonly used in the design and publishing industries to fill a space on a page and give an impression of how the final content will look. It is derived from a Latin text by the Roman philosopher Cicero and has been used since the 1960s. The text is nonsensical and does not convey any specific meaning, allowing designers to focus on layout and visual elements without the distraction of meaningful content.
https://xakep.ru/
"""

@pytest.mark.parametrize("content,display_name,link_preview", [
    (content_wo_link, None, False),
    (content_wo_link, 'Botov Bot Botovich', False),
    (content_w_link, None, False),
    (content_w_link, None, True),
])
def test_create_message(bot: Pachca, chat: dict, content: str, display_name: str, link_preview: bool):
    """
    Test for `create message` method.

    Args:
        bot (Pachca): Pachca API client instance with bot access token.
        chat (dict): Created chat dict.
        content (str): Thread message content.
        display_name (str): Thread message display name.
        link_preview (bool): Thread message link preview flag.
    """
    created_message = bot.create_message(
        entity_id=chat['id'],
        entity_type='discussion',
        content=content,
        display_name=display_name,
        link_preview=link_preview
    )
    received_message = bot.get_message(created_message['id'])

    assert received_message['content'] == content
    assert received_message['display_name'] == display_name


def test_update_message(bot: Pachca, chat: dict):
    """
    Test for `update message` method.

    Args:
        bot (Pachca): Pachca API client instance with bot access token.
        chat (dict): Created chat dict.
    """
    created_message = bot.create_message(
        entity_id=chat['id'],
        entity_type='discussion',
        content=content_wo_link
    )
    assert created_message['content'] == content_wo_link

    updated_message = bot.update_message(
        message_id=created_message['id'],
        content=content_w_link
    )
    assert updated_message['content'] == content_w_link


@pytest.fixture(scope="module")
def thread(bot: Pachca, admin: Pachca, chat: dict):

    message = bot.create_message(
        entity_id=chat['id'],
        entity_type='discussion',
        content=content_w_link,
        display_name='Bot Thread',
        link_preview=True
    )
    thread = bot.create_thread(message_id=message['id'])
    yield thread


@pytest.mark.parametrize("content,display_name,link_preview", [
    ('Comment 1', None, False),
    ('Comment 2', 'Botov Bot Botovich', False),
    ('Comment 3', None, False),
    ('Comment 4 (https://ya.ru)', None, True),
])
def test_create_thread(bot: Pachca, thread: dict, content: str, display_name: str, link_preview: bool):
    """
    Test for `create thread` method.

    Args:
        bot (Pachca): Pachca API client instance with bot access token.
        thread (dict): Created thread dict.
        content (str): Thread message content.
        display_name (str): Thread message display name.
        link_preview (bool): Thread message link preview flag.
    """
    created_message = bot.create_message(
        entity_id=thread['id'],
        entity_type='thread',
        content=content,
        display_name=display_name,
        link_preview=link_preview
    )
    received_message = bot.get_message(created_message['id'])

    assert received_message['content'] == content
    assert received_message['display_name'] == display_name


def test_pin_message(bot: Pachca, chat: dict):
    """
    Test for `pin/unpin message` methods.

    Args:
        bot (Pachca): Pachca API client instance with bot access token.
        chat (dict): Created chat dict.
    """
    created_message = bot.create_message(
        entity_id=chat['id'],
        entity_type='discussion',
        content=content_w_link,
        display_name='Bot Pin/Unpin',
        link_preview=True
    )
    received_message = bot.get_message(created_message['id'])

    bot.pin_message(received_message['id'])
    bot.unpin_message(received_message['id'])


def test_get_messages(bot: Pachca, chat: dict):
    """
    Test for `get messages` methods.

    Args:
        bot (Pachca): Pachca API client instance with bot access token.
        chat (dict): Created chat dict.
    """
    messages = bot.get_messages(chat['id'])
    assert isinstance(messages, list)


def test_delete_message(bot: Pachca, admin: Pachca, chat: dict):
    """
    Delete message test.

    Args:
        bot (Pachca): Pachca API client instance with bot access token.
        admin (Pachca): Pachca API client instance with admin access token.
        chat (dict): Chat fixture.
    """
    created_message = bot.create_message(
        entity_id=chat['id'],
        entity_type='discussion',
        content=content_w_link,
        display_name='Bot Delete',
        link_preview=True
    )
    time.sleep(1)
    admin.delete_message(created_message['id'])