# -*- coding: utf-8 -*-

import json

from rpi.dns import RpiDns
from rpi.exceptions import MissingKeyError
from rpi.rpi_logging import Logger

logger = Logger.get(__file__, __name__)


class KeyManager(object):
    # TODO: improve: I can use some kind of token, and store them in a sqlite database or at least encrypt the json.
    """Manages the passwords."""

    def __init__(self):
        super().__init__()
        self.path = RpiDns.get('json.claves')
        with open(self.path) as f:
            self.dict = json.load(f)

    @staticmethod
    def keys():
        self = object.__new__(KeyManager)
        self.__init__()

        return tuple(self.dict.keys())

    def save(self):
        if self.dict is not None:
            with open(self.path, 'wt') as f:
                json.dump(self.dict, f, ensure_ascii=False, indent=4, sort_keys=True)

    @staticmethod
    def set(service, password):
        self = object.__new__(KeyManager)
        self.__init__()

        self.dict[service] = password
        self.save()

    @staticmethod
    def get(key):
        self = object.__new__(KeyManager)
        self.__init__()

        logger.debug(f'Finding key for {key!r}')

        if key not in self.keys():
            logger.critical(f'Key {key!r} not found')
            raise MissingKeyError(f'Key {key!r} not found')

        return self.dict[key]
