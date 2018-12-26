# -*- coding: utf-8 -*-

import requests
from requests.exceptions import ConnectionError

from .exceptions import DownloaderError
from .rpi_logging import Logger

logger = Logger.get(__file__, __name__)


class Downloader(requests.Session):
    """Downloader with retries control."""

    def __init__(self, retries=10, silenced=False):

        global logger
        if silenced is True:
            Logger.silence(logger)

        self._retries = retries
        super().__init__()

    def get(self, *args, **kwargs):
        logger.debug(f'GET {args[0]!r}')
        retries = self._retries

        while retries > 0:
            try:
                return super().get(*args, **kwargs)
            except ConnectionError:
                retries -= 1
                logger.warning(f'Connection error in GET, retries={retries}')

        logger.critical(f'Download error in GET {args[0]!r}')
        raise DownloaderError('max retries failed.')

    def post(self, *args, **kwargs):
        logger.debug(f'POST {args[0]!r}')
        retries = self._retries

        while retries > 0:
            try:
                return super().post(*args, **kwargs)
            except ConnectionError:
                retries -= 1
                logger.warning('Connection error in POST, retries=' + str(retries))

        logger.critical(f'Download error in POST {args[0]!r}')
        raise DownloaderError('max retries failed.')
