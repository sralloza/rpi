# -*- coding: utf-8 -*-

import requests

from requests.exceptions import ConnectionError

from .exceptions import DownloaderError
from .rpi_logging import Logger

logger = Logger.get(__file__, __name__)


class Downloader(requests.Session):
    def __init__(self, retries=10):
        self._retries = retries
        super().__init__()

    def get(self, *args, **kwargs):
        logger.debug('GET ' + args[0])
        retries = self._retries

        while retries > 0:
            try:
                return super().get(*args, **kwargs)
            except ConnectionError:
                retries -= 1
                logger.warning('Connection error in GET, retries=' + str(retries))

        logger.critical('Error de descarga en GET ' + args[0])
        raise DownloaderError('max retries failed.')

    def post(self, *args, **kwargs):
        logger.debug('POST ' + args[0])
        retries = self._retries

        while retries > 0:
            try:
                return super().post(*args, **kwargs)
            except ConnectionError:
                retries -= 1
                logger.warning('Connection error in POST, retries=' + str(retries))

        logger.critical('Error de descarga en POST ' + args[0])
        raise DownloaderError('max retries failed.')
