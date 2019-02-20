# -*- coding: utf-8 -*-

"""Password manager for raspberry pi scripts."""

import json
import logging
from typing import Tuple

from rpi.dns import RpiDns
from rpi.exceptions import MissingKeyError


class KeysManager:
    # TODO: improve: I can use some kind of token, and store them in a sqlite database or at
    #  least encrypt the json.
    """Manages the passwords."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.path = RpiDns.get('json.claves')

        try:
            with open(self.path) as file_handler:
                self.dict = json.load(file_handler)
        except FileNotFoundError:
            self.logger.critical('Keys file not found (%r)', self.path)
            raise FileNotFoundError(f'Keys file not found ({self.path!r})')

    @staticmethod
    def keys() -> Tuple[str]:
        """Returns all the keys for the passwords.

        Returns:
            Tuple[str]: keys of the passwords

        """
        self = object.__new__(KeysManager)
        self.__init__()

        result = tuple(self.dict.keys())

        self.logger.debug('Returning list of keys - %r', result)

        return result

    def save(self):
        """Saves the passwords."""
        if self.dict is not None:
            with open(self.path, 'wt') as file_handler:
                json.dump(self.dict, file_handler, ensure_ascii=False, indent=4, sort_keys=True)

        self.logger.debug('Saved keys successfully')

    def delete(self, service):
        if service not in self.keys():
            self.logger.critical('Key %r not found', service)
            raise MissingKeyError(f'Key {service!r} not found')

        del self.dict[service]
        self.logger.debug('Deleted password of service %r', service)

        self.save()

    @staticmethod
    def set(service: str, password: str):
        """Sets a password  given its password and service.

        Args:
            service (str): service of the password.
            password (str): password to store.

        """
        self = object.__new__(KeysManager)
        self.__init__()

        self.logger.debug('Saving password for key %r', service)

        self.dict[service] = password
        self.save()

    @staticmethod
    def get(key: str) -> str:
        """Returns the password of the key.

        Args:
            key (str): service of the password to get.

        Returns:
            str: password.

        """
        self = object.__new__(KeysManager)
        self.__init__()

        self.logger.debug('Searching key for %r', key)

        if key not in self.keys():
            self.logger.critical('Key %r not found', key)
            raise MissingKeyError(f'Key {key!r} not found')

        self.logger.debug('Password found for key %r', key)

        return self.dict[key]
