# -*- coding: utf-8 -*-

import datetime
import logging
import os
import platform

from .dns import RpiDns
from .exceptions import WrongCalledError


class Logging(logging.Logger):
    """Logging personal para todos los scripts."""
    DEFAULT_LEVEL_WINDOWS = logging.DEBUG
    DEFAULT_LEVEL_LINUX = logging.DEBUG

    NOMBRE = None

    CREATED = False
    SEPARATED = False

    def __init__(self, name):

        super().__init__(name)
        raise WrongCalledError('Use get instead')

    @staticmethod
    def silence(logger):
        handler: logging.Handler = logger.handlers[-1]
        handler.setLevel(logging.CRITICAL)

    @staticmethod
    def get(archivo: str, nombre: str, windows_level: int = None, linux_level: int = None, setglobal=False):
        """Genera un logger."""

        hoy = datetime.datetime.today().strftime('%Y-%m-%d')

        if nombre == '__main__':
            name = '<' + os.path.basename(archivo)[:os.path.basename(archivo).rfind('.')] + '>'
            Logging.NOMBRE = name
        else:
            name = nombre

        windows_level = Logging.DEFAULT_LEVEL_WINDOWS if windows_level is None else windows_level
        linux_level = Logging.DEFAULT_LEVEL_LINUX if linux_level is None else linux_level

        logger = logging.getLogger(name)
        if not logger.handlers:
            # Prevent logging from propagating to the root logger
            logger.propagate = 0

            # logging_format = '[%(asctime)s] %(levelname)s - %(name)s - %(module)s:%(lineno)s: %(message)s'
            logging_format = '[%(asctime)s] %(levelname)s - %(name)s:%(lineno)s: %(message)s'
            time_format = '%H:%M:%S'

            logs_folder = RpiDns.get('folder.logs')

            if os.path.isdir(logs_folder) is False:
                os.mkdir(logs_folder)

            if logs_folder.endswith('/') is False:
                logs_folder += '/'

            if os.path.isdir(logs_folder) is False:
                os.mkdir(logs_folder)

            filename = logs_folder + hoy + '.log'

            Logging.CREATED = True

            formatter = logging.Formatter(logging_format, time_format)

            filehandler = logging.FileHandler(filename, 'a', 'utf-8')
            filehandler.setFormatter(formatter)
            logger.addHandler(filehandler, )

            if platform.system() == 'Windows':
                logger.setLevel(windows_level)
            else:
                logger.setLevel(linux_level)

            if setglobal is True:
                logging.basicConfig(level=windows_level, format=logging_format, datefmt=time_format, filename=filename)

        return logger
