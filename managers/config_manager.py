# -*- coding: utf-8 -*-

from rpi.dns import RpiDns
from rpi.exceptions import ConfigNotFoundError, EmptyConfigError


class ConfigManager(object):
    def __init__(self):
        super(ConfigManager, self).__init__()
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
        try:
            with open(self.path, 'rt', encoding='utf-8') as fh:
                data = fh.read()
        except FileNotFoundError:
            raise FileNotFoundError(f'Config file does not exist ({self.path!r})')

        for line in data.splitlines():
            key, *value = line.split('=')

            key = key.strip()
            value = '='.join(value).strip()

            self[key] = value

    def save(self, force=False):
        if len(self) == 0 and force is False:
            raise EmptyConfigError('There are no configurations to save')
        with open(self.path, 'wt', encoding='utf-8') as fh:
            for key, value in self.config.items():
                fh.write(f"{key}={value}\n")

    @staticmethod
    def get(config):
        self = ConfigManager.__new__(ConfigManager)
        self.__init__()

        if config not in self:
            raise ConfigNotFoundError(f'Configuration not found: {config!r}')

        valor = self[config]

        return valor

    @staticmethod
    def set(config, value):
        self = ConfigManager.__new__(ConfigManager)
        self.__init__()

        self[config] = value

        self.save()

    @staticmethod
    def delete(config):
        self = ConfigManager.__new__(ConfigManager)
        self.__init__()

        del self[config]
        self.save(force=True)

    @staticmethod
    def list():
        self = ConfigManager.__new__(ConfigManager)
        self.__init__()

        return tuple(self.config.keys())
