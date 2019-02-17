import os
import random
import string

import pytest

from rpi.exceptions import UserNotFoundError
from rpi.launcher import TelegramLauncher
from rpi.managers.crontab_manager import CrontabManager
from rpi.managers.users_manager import UsersManager


def random_string(n):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))


@pytest.mark.xfail(condition='test' not in UsersManager(), reason="User 'test' not found.")
class TestUser:
    def test_update_cronitems(self):
        test = UsersManager.get_by_username('test')

        assert len(test.cronitems) == 0

        test.new_task('/home/test/command', 'test', 11, 11)

        assert len(test.cronitems) > 0

        for job in CrontabManager.list_by_user('test'):
            CrontabManager.delete_by_anything(job)

        test.update_cronitems()
        assert len(test.cronitems) == 0


@pytest.mark.xfail(condition='test' not in UsersManager(), reason="User 'test' not found.")
class TestUsersManager:
    def test_usernames(self):
        assert len(UsersManager().usernames) > 0

    def test_emails(self):
        assert len(UsersManager().emails) > 0

    def test_bet_by_username(self):
        UsersManager.get_by_username('test')

        random_user = random_string(20)

        with pytest.raises(UserNotFoundError, match=random_user):
            UsersManager.get_by_username(random_user)

    def test_save_launcher(self):
        test = UsersManager.get_by_username('test')
        test.launcher = TelegramLauncher(-1)
        um = UsersManager()
        um.save_launcher(test)


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__), '-v'])
