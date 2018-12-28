# -*- coding: utf-8 -*-

import json

from rpi.dns import RpiDns
from rpi.exceptions import MissingKeyError
from rpi.rpi_logging import Logging


class KeysManager(object):
    # TODO: improve: I can use some kind of token, and store them in a sqlite database or at least encrypt the json.
    """Manages the passwords."""

    def __init__(self):
        self.logger = Logging.get(__file__, __name__)
        self.path = RpiDns.get('json.claves')
        with open(self.path) as f:
            self.dict = json.load(f)

    @staticmethod
    def keys():
        self = object.__new__(KeysManager)
        self.__init__()

        result = tuple(self.dict.keys())

        self.logger.debug(f'Returning list of keys - {result!r}', {'show': False})

        return result

    def save(self):
        if self.dict is not None:
            with open(self.path, 'wt') as f:
                json.dump(self.dict, f, ensure_ascii=False, indent=4, sort_keys=True)

        self.logger.debug(f'Saved keys successfully')

    @staticmethod
    def set(service, password):
        self = object.__new__(KeysManager)
        self.__init__()

        self.logger.debug(f'Saving password for key {service!r}')

        self.dict[service] = password
        self.save()

    @staticmethod
    def get(key):
        self = object.__new__(KeysManager)
        self.__init__()

        self.logger.debug(f'Searching key for {key!r}', {'show': False})

        if key not in self.keys():
            self.logger.critical(f'Key {key!r} not found')
            raise MissingKeyError(f'Key {key!r} not found')

        self.logger.debug(f'Password found for key {key!r}')

        return self.dict[key]
