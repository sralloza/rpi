# -*- coding: utf-8 -*-

"""Custom downloader with retries control."""

import logging

import requests

from .exceptions import DownloaderError

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}


class Downloader(requests.Session):
    """Downloader with retries control."""

    def __init__(self, retries=10, silenced=False):
        self.logger = logging.getLogger(__name__)

        if silenced is True:
            self.logger.handlers = []

        self._retries = retries
        super().__init__()

    def get(self, url, **kwargs):
        self.logger.debug('GET %r', url)
        retries = self._retries

        while retries > 0:
            try:
                return super().get(url, **kwargs)
            except requests.exceptions.ConnectionError:
                retries -= 1
                self.logger.warning('Connection error in GET, retries=%s', retries)

        self.logger.critical('Download error in GET %r', url)
        raise DownloaderError('max retries failed.')

    def post(self, url, data=None, json=None, **kwargs):
        self.logger.debug('POST %r', url)
        retries = self._retries

        while retries > 0:
            try:
                return super().post(url=url, data=data, json=json, **kwargs)
            except requests.exceptions.ConnectionError:
                retries -= 1
                self.logger.warning('Connection error in POST, retries=%s', retries)

        self.logger.critical('Download error in POST %r', url)
        raise DownloaderError('max retries failed.')
