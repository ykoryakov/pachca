import uuid
import logging
import time

import pytest

from pachca import Pachca

logger = logging.getLogger()


@pytest.fixture(scope="function")
def chat(bot: Pachca, admin: Pachca):
    name = str(uuid.uuid4())[:4]
    chat = bot.create_chat(
        name=name,
        member_ids=[],
        group_tag_ids=[],
        channel=False,
        public=False,
        ignore_existing=True
    )
    yield chat
    time.sleep(1)
    bot.add_member(
        chat_id=chat['id'],
        member_ids=[admin.get_user_id()]
    )
    admin.archive_chat(chat['id'])

def test_add_member(bot: Pachca, admin: Pachca, chat: dict):
    """
    Test for `add member` method.

    Args:
        bot (Pachca): Pachca API client instance with bot access token.
        chat (dict): Created chat dict.
    """
    member_id = admin.get_user_id()

    bot.add_member(
        chat_id=chat['id'],
        member_ids=[member_id]
    )

    members = bot.get_members(
        chat_id=chat['id']
    )

    assert len(members) == 2  # owner + member

    member = bot.get_member(
        chat_id=chat['id'],
        member_id=member_id
    )

    assert member['id'] == member_id

    bot.update_member(
        chat_id=chat['id'],
        member_id=member_id,
        role='admin'
    )

    assert member['role'] == 'admin'

    bot.remove_member(
        chat_id=chat['id'],
        member_id=member_id
    )

    members = bot.get_members(
        chat_id=chat['id']
    )

    assert len(members) == 1  # owner (member removed)
