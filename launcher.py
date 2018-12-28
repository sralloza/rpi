# -*- coding: utf-8 -*-
from telegram import Bot

from rpi.managers.config_manager import ConfigManager
from .downloader import Downloader
from .exceptions import DownloaderError, UserError
from .rpi_logging import Logging


class BaseLauncher(object):
    """Clase base para lanzar notificadores."""

    def __init__(self, downloader=None):
        if downloader is None:
            self._downloader = Downloader()
        else:
            self._downloader = downloader

        self.logger = Logging.get(__file__, __name__)
        self.url = None
        self.chat_id = None
        self.code = None

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


class InvalidLauncher(BaseLauncher):

    def fire(self, title, message):
        raise NotImplementedError

    def to_json(self):
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
            self.logger.debug('IftttLauncher Fired')
        except DownloaderError:
            self.logger.error('DownloadError in IftttLauncher')

    def to_json(self):
        return {"type": "IFTTT", "url": self.url}


class TelegramLauncher(BaseExtendedLauncher):
    def __init__(self, chat_id_or_code: str, downloader=None):
        super().__init__(downloader)

        chat_id_or_code = str(chat_id_or_code)

        if chat_id_or_code.isdigit():
            self.chat_id = int(chat_id_or_code)
            self.code = None
        else:
            self.chat_id = None
            self.code = chat_id_or_code

    def fire(self, title, message):
        bot = Bot(ConfigManager.get('telegram_bot_token'))

        if self.chat_id is None:
            self.logger.critical('User not confirmed')
            raise UserError('User not confirmed')

        complete_message = title + ':\n' + message
        bot.send_message(chat_id=self.chat_id, text=complete_message)
        self.logger.debug('TelegramLauncher Fired')

    def to_json(self):
        self.update_status()
        return {"type": "Telegram", "chat_id": self.chat_id, "url": self.code}

    def update_status(self):
        if self.chat_id is not None:
            self.code = ''


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
            self.logger.debug('NotifyRunLauncher Fired')
        except DownloaderError:
            self.logger.error('DownloadError in NotifyRunLauncher')

    def to_json(self):
        return {"type": "NotifyRun", "url": self.url}
