# -*- coding: utf-8 -*-

import datetime
import logging
import os
import platform

from .dns import RpiDns
from .exceptions import WrongCalledError


class RpiLogger(logging.Logger):
    def __init__(self, name):
        super().__init__(name)

    def log(self, level, msg, *args, enable=True, **kwargs):
        if enable is True:
            super().log(level, msg, *args, **kwargs)

    def info(self, msg, *args, enable=True, **kwargs):
        return self.log(logging.INFO, msg, *args, enable=enable, **kwargs)

    def debug(self, msg, *args, enable=True, **kwargs):
        return self.log(logging.DEBUG, msg, *args, enable=enable, **kwargs)

    def warning(self, msg, *args, enable=True, **kwargs):
        return self.log(logging.WARNING, msg, *args, enable=enable, **kwargs)

    def error(self, msg, *args, enable=True, **kwargs):
        return self.log(logging.ERROR, msg, *args, enable=enable, **kwargs)

    def critical(self, msg, *args, enable=True, **kwargs):
        return self.log(logging.CRITICAL, msg, *args, enable=enable, **kwargs)


logging.setLoggerClass(RpiLogger)


class Logging(object):  # (logging.Logger):
    """Logging personal para todos los scripts."""
    DEFAULT_LEVEL_WINDOWS = logging.DEBUG
    DEFAULT_LEVEL_LINUX = logging.DEBUG

    ROYAL = None
    WARNED = False

    LOGGING_FORMAT = '[%(asctime)s] %(levelname)-8s - %(name)s:%(lineno)s: %(message)s'
    TIME_FORMAT = '%H:%M:%S'

    today = datetime.datetime.today()

    LOGS_GENERAL_FOLDER = RpiDns.get('folder.logs')
    LOGS_YEAR_FOLDER = os.path.join(LOGS_GENERAL_FOLDER, str(today.year))
    LOGS_MONTH_FOLDER = os.path.join(LOGS_YEAR_FOLDER, str(today.month))

    if os.path.isdir(LOGS_GENERAL_FOLDER) is False:
        os.mkdir(LOGS_GENERAL_FOLDER)

    if os.path.isdir(LOGS_YEAR_FOLDER) is False:
        os.mkdir(LOGS_YEAR_FOLDER)

    if os.path.isdir(LOGS_MONTH_FOLDER) is False:
        os.mkdir(LOGS_MONTH_FOLDER)

    LOG_FILENAME = os.path.join(LOGS_MONTH_FOLDER, str(today.day) + '.log')

    def __init__(self, name):

        super().__init__(name)
        raise WrongCalledError('Use get instead')

    @staticmethod
    def silence(logger):
        handler: logging.Handler = logger.handlers[-1]
        handler.setLevel(logging.CRITICAL)

    @staticmethod
    def get(archivo: str, nombre: str, windows_level: int = None, linux_level: int = None,
            setglobal=False) -> RpiLogger:
        """Returns a custom logger."""

        warning = False

        if nombre == '__main__':
            Logging.ROYAL = os.path.basename(archivo)[:os.path.basename(archivo).rfind('.')]
            name = '<' + Logging.ROYAL + '>'
        else:
            if Logging.ROYAL is None:
                warning = True
            name = str(Logging.ROYAL) + ' - ' + nombre

        windows_level = Logging.DEFAULT_LEVEL_WINDOWS if windows_level is None else windows_level
        linux_level = Logging.DEFAULT_LEVEL_LINUX if linux_level is None else linux_level

        logger: RpiLogger = logging.getLogger(name)

        if not logger.handlers:
            # Prevent logging from propagating to the root logger
            logger.propagate = 0

            # logging_format = '[%(asctime)s] %(levelname)s - %(name)s - %(module)s:%(lineno)s: %(message)s'

            formatter = logging.Formatter(Logging.LOGGING_FORMAT, Logging.TIME_FORMAT)

            filehandler = logging.FileHandler(Logging.LOG_FILENAME, 'a', 'utf-8')
            filehandler.setFormatter(formatter)
            logger.addHandler(filehandler)

            if platform.system() == 'Windows':
                logger.setLevel(windows_level)
            else:
                logger.setLevel(linux_level)

            if setglobal is True:
                logging.basicConfig(level=windows_level, format=Logging.LOGGING_FORMAT, datefmt=Logging.TIME_FORMAT,
                                    filename=Logging.LOG_FILENAME)

        if warning is True and Logging.WARNED is False:
            logger.warning('No se ha declarado un logger principal')
            Logging.WARNED = True
        return logger
