import datetime
import os
import random
import string

import pytest

from rpi.exceptions import ConfigNotFoundError, ConfigError
from rpi.managers.config_manager import ConfigManager


class TestConfigManager:
    @pytest.fixture(scope='class')
    def codename(self):
        return 'test-' + str(datetime.datetime.today().date())

    def test_load(self):
        ConfigManager()

    def test_get_and_set(self, codename):
        with pytest.raises(ConfigNotFoundError, match='test'):
            ConfigManager.get(codename)

        ConfigManager.set(codename, 'True')
        ConfigManager.get(codename)

    def test_save(self, codename):
        ConfigManager.get(codename)

    def test_delete(self, codename):
        random_word = ''.join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(15))

        ConfigManager.delete(codename)

        with pytest.raises(ConfigError, match='Config not found'):
            ConfigManager.delete(random_word)

    def test_list(self):
        config_list = ConfigManager.list()
        assert len(config_list) >= 0
        assert isinstance(config_list, (tuple, list))


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__), '-v'])
