# -*- coding: utf-8 -*-

from .downloader import Downloader
from .exceptions import DownloaderError
from .rpi_logging import Logger

logger = Logger.get(__file__, __name__)


class BaseLauncher(object):
    """Clase base para lanzar notificadores."""

    def __init__(self, downloader=None):
        if downloader is None:
            self._downloader = Downloader()
        else:
            self._downloader = downloader

    def __repr__(self):
        return str(self)

    def __str__(self):
        return type(self).__name__

    def fire(self, title, message):
        """Lanza un mensaje con la información ``data``."""
        raise NotImplementedError

    def to_json(self):
        """Devuelve el launcher serializado en json."""
        raise NotImplementedError


class BaseExtendedLauncher(BaseLauncher):
    """Clase base para Launchers que permiten mensajes multilínea."""

    def fire(self, title, message):
        raise NotImplementedError

    def to_json(self):
        raise NotImplementedError


class BaseMinimalLauncher(BaseLauncher):
    """Clase base para Launchers que no permiten mensajes multilínea."""

    def fire(self, title, message):
        raise NotImplementedError

    def to_json(self):
        raise NotImplementedError


class IftttLauncher(BaseExtendedLauncher):
    """Lanzador implementado con el servicio IFTTT."""

    def __init__(self, url, downloader=None):
        super().__init__(downloader)
        self.url = url

    def fire(self, title, message):
        report = {'value1': title, 'value2': message}
        try:
            self._downloader.post(self.url, data=report)
            logger.debug('IftttLauncher Fired')
        except DownloaderError:
            logger.error('Error de notificación en IftttLauncher')

    def to_json(self):
        return {"tipo": "IFTTT", "url": self.url}


class NotifyRunLauncher(BaseMinimalLauncher):
    """Lanzador implementado con el servicio Notify.me."""

    def __init__(self, url, downloader=None):
        super().__init__(downloader)
        while '/c/' in url:
            url = url.replace('/c/', '/')
        self.url = url

    def fire(self, title, message):
        try:
            self._downloader.post(self.url, {'message': message})
            logger.debug('NotifyRunLauncher Fired')
        except DownloaderError:
            logger.error('Error de notificación en NotifyRunLauncher')

    def to_json(self):
        return {"tipo": "NotifyRun", "url": self.url}
