# -*- coding: utf-8 -*-

"""Configuration manager for raspberry pi.
Designed to easilly use and store pairs of key - value.
"""
import logging

from rpi.dns import RpiDns
from rpi.exceptions import ConfigNotFoundError, EmptyConfigError, ConfigError


class ConfigManager:
    """Configuration manager."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.path = RpiDns.get('textdb.config')
        self.config = {}
        self.load()

    def __setitem__(self, key, value):
        self.config[key] = value

    def __getitem__(self, item):
        try:
            return self.config[item]
        except KeyError:
            raise ConfigError(f'Config not found: {item!r}')

    def __delitem__(self, key):
        del self.config[key]

    def __iter__(self):
        return iter(self.config)

    def __len__(self):
        return len(self.config)

    def __contains__(self, item):
        return item in self.config

    def load(self):
        """Loads configurations from the main file."""

        self.logger.debug('Loading config')
        try:
            with open(self.path, 'rt', encoding='utf-8') as file_handler:
                data = file_handler.read()
        except FileNotFoundError:
            self.logger.critical('Config file does not exist (%r)', self.path)
            raise FileNotFoundError(f'Config file does not exist ({self.path!r})')

        for line in data.splitlines():
            key, *value = line.split('=')

            key = key.strip()
            value = '='.join(value).strip()

            self[key] = value

    def save(self, force: bool = False):
        """Saves all the configurations in the file.

        Args:
            force (bool): tells the function to save configurations even if there are no
                configurations to save.

        Raises:
             EmptyConfigError: if there are no configurations to save and force is False.
             ConfigError: if the user is trying to save less configurations than the ones that
                are currently saved.

        """

        other = ConfigManager.__new__(ConfigManager)
        other.__init__()

        if len(other) > len(self) and force is False:
            self.logger.critical(
                'You can not save less configurations than the ones that are saved')
            raise ConfigError('You can not save less configurations than the ones that are saved')

        if len(self) == 0 and force is False:
            self.logger.critical('There are no configurations to save')
            raise EmptyConfigError('There are no configurations to save')

        with open(self.path, 'wt', encoding='utf-8') as file_handler:
            for key, value in self.config.items():
                file_handler.write(f"{key}={value}\n")

        self.logger.debug('Configurations saved (force=%s)', force)

    @staticmethod
    def get(config: str) -> str:
        """Gets a configuration value by its key.

        Args:
            config (str): key for the configuration.

        Returns:
            str:  value for the configuration.

        """
        self = ConfigManager.__new__(ConfigManager)
        self.__init__()

        if config not in self:
            self.logger.critical('Configuration not found: %r', config)
            raise ConfigNotFoundError(f'Configuration not found: {config!r}')

        valor = self[config]

        # self.logger.debug(f'Returning config value {valor!r} from key {config!r}')

        return valor

    @staticmethod
    def set(config: str, value: str):
        """Sets a configuration value using its key.

        Args:
            config (str): key of the configuration.
            value (str): value of the configuration.

        """

        self = ConfigManager.__new__(ConfigManager)
        self.__init__()

        self[config] = value

        self.logger.debug('Set config value %r with key %r', value, config)

        self.save()

    @staticmethod
    def delete(config: str):
        """Deletes a configuration using its key.

        Args:
            config (str): configuration key.

        """

        self = ConfigManager.__new__(ConfigManager)
        self.__init__()

        value_to_delete = self[config]

        del self[config]
        self.logger.debug('Deleted config value %r with key %r', value_to_delete, config)
        self.save(force=True)

    @staticmethod
    def list() -> tuple:
        """Returns a list of the keys of the configurations.

        Returns:
            Tuple[str]: tuple with all the keys.
        """
        self = ConfigManager.__new__(ConfigManager)
        self.__init__()

        result = tuple(self.config.keys())

        self.logger.debug('Returning config keys - %s', result)

        return result
