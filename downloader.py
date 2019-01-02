# -*- coding: utf-8 -*-

import requests
from requests.exceptions import ConnectionError

from .exceptions import DownloaderError
from .rpi_logging import Logging

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}


class Downloader(requests.Session):
    """Downloader with retries control."""

    def __init__(self, retries=10, silenced=False):
        self.logger = Logging.get(__file__, __name__)

        if silenced is True:
            Logging.silence(self.logger)

        self._retries = retries
        super().__init__()

    def get(self, *args, **kwargs):
        self.logger.debug(f'GET {args[0]!r}')
        retries = self._retries

        while retries > 0:
            try:
                return super().get(*args, **kwargs)
            except ConnectionError:
                retries -= 1
                self.logger.warning(f'Connection error in GET, retries={retries}')

        self.logger.critical(f'Download error in GET {args[0]!r}')
        raise DownloaderError('max retries failed.')

    def post(self, *args, **kwargs):
        self.logger.debug(f'POST {args[0]!r}')
        retries = self._retries

        while retries > 0:
            try:
                return super().post(*args, **kwargs)
            except ConnectionError:
                retries -= 1
                self.logger.warning('Connection error in POST, retries=' + str(retries))

        self.logger.critical(f'Download error in POST {args[0]!r}')
        raise DownloaderError('max retries failed.')
