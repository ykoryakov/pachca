import logging

from pachca import Pachca

logger = logging.getLogger()


def test_profile(bot: Pachca, admin: Pachca):
    """
    Test for `get profile` method.

    Args:
        bot (Pachca): Pachca API client instance with bot access token.
        admin (Pachca): Pachca API client instance with admin access token.
    """
    for _client in (bot, admin):
        profile = _client.get_profile()
        assert isinstance(profile['id'], int)
