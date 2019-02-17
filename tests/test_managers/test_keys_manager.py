import os
import random
import string

import pytest

from rpi.exceptions import MissingKeyError
from rpi.managers.keys_manager import KeysManager


class TestKeysManager:
    def test_set(self):
        KeysManager.set('test_service', 'test_password')

    def test_get(self):
        assert KeysManager.get('test_service') == 'test_password'

        random_service = ''.join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(15))

        with pytest.raises(MissingKeyError, match=random_service):
            KeysManager.get(random_service)

    def test_delete(self):
        km = KeysManager()
        km.delete('test_service')

        with pytest.raises(MissingKeyError, match='test_service'):
            KeysManager.get('test_service')


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__), '-v'])
