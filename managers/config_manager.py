# -*- coding: utf-8 -*-

from rpi.dns import RpiDns
from rpi.exceptions import ConfigNotFoundError, EmptyConfigError, ConfigError
from rpi.rpi_logging import Logging


class ConfigManager(object):
    def __init__(self):
        self.logger = Logging.get(__file__, __name__)
        self.path = RpiDns.get('textdb.config')
        self.config = {}
        self.load()

    def __setitem__(self, key, value):
        self.config[key] = value

    def __getitem__(self, item):
        return self.config[item]

    def __delitem__(self, key):
        del self.config[key]

    def __iter__(self):
        return iter(self.config)

    def __len__(self):
        return len(self.config)

    def __contains__(self, item):
        return item in self.config

    def load(self):
        # self.logger.debug('Loading config')
        try:
            with open(self.path, 'rt', encoding='utf-8') as fh:
                data = fh.read()
        except FileNotFoundError:
            self.logger.critical(f'Config file does not exist ({self.path!r})')
            raise FileNotFoundError(f'Config file does not exist ({self.path!r})')

        for line in data.splitlines():
            key, *value = line.split('=')

            key = key.strip()
            value = '='.join(value).strip()

            self[key] = value

    def save(self, force=False):

        other = ConfigManager.__new__(ConfigManager)
        other.__init__()

        if len(other) > len(self):
            self.logger.critical('You can not save less configurations than the ones that are saved')
            raise ConfigError('You can not save less configurations than the ones that are saved')

        if len(self) == 0 and force is False:
            self.logger.critical('There are no configurations to save')
            raise EmptyConfigError('There are no configurations to save')

        with open(self.path, 'wt', encoding='utf-8') as fh:
            for key, value in self.config.items():
                fh.write(f"{key}={value}\n")

        self.logger.debug(f'Configurations saved (force={force})')

    @staticmethod
    def get(config):
        self = ConfigManager.__new__(ConfigManager)
        self.__init__()

        if config not in self:
            self.logger.critical(f'Configuration not found: {config!r}')
            raise ConfigNotFoundError(f'Configuration not found: {config!r}')

        valor = self[config]

        # self.logger.debug(f'Returning config value {valor!r} from key {config!r}')

        return valor

    @staticmethod
    def set(config, value):
        self = ConfigManager.__new__(ConfigManager)
        self.__init__()

        self[config] = value

        self.logger.debug(f'Set config value {value!r} with key {config!r}')

        self.save()

    @staticmethod
    def delete(config):
        self = ConfigManager.__new__(ConfigManager)
        self.__init__()

        value_to_delete = self[config]

        del self[config]
        self.logger.debug(f'Deleted config value {value_to_delete!r} with key {config!r}')
        self.save(force=True)

    @staticmethod
    def list():
        self = ConfigManager.__new__(ConfigManager)
        self.__init__()

        result = tuple(self.config.keys())

        self.logger.debug(f'Returning config keys - {result}', {'show': False})

        return result
