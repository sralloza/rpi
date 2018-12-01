# -*- coding: utf-8 -*-

import datetime
import logging
import os
import platform
import re

from .dns import RpiDns
from .exceptions import WrongLogType


class Logger:
    """Logger personal para todos los scripts."""
    DEFAULT_LEVEL_WINDOWS = logging.DEBUG
    DEFAULT_LEVEL_LINUX = logging.DEBUG

    DEFAULT_LOG_WINDOWS = 'file'
    DEFAULT_LOG_LINUX = 'file'
    NOMBRE = None
    ID = None

    CREATED = False
    SEPARATED = False

    @staticmethod
    def get(archivo: str, nombre, windows_level: int = None, linux_level: int = None, windows_log=None, linux_log=None):
        """Genera un logger."""

        hoy = datetime.datetime.today().strftime('%Y-%m-%d')

        if nombre == '__main__':
            name = '<' + os.path.basename(archivo)[:os.path.basename(archivo).rfind('.')] + '>'
            Logger.NOMBRE = name
        else:
            name = nombre

        windows_level = Logger.DEFAULT_LEVEL_WINDOWS if windows_level is None else windows_level
        linux_level = Logger.DEFAULT_LEVEL_LINUX if linux_level is None else linux_level
        windows_log = Logger.DEFAULT_LOG_WINDOWS if windows_log is None else windows_log
        linux_log = Logger.DEFAULT_LOG_LINUX if linux_log is None else linux_log

        logger = logging.getLogger(name)
        if not logger.handlers:
            # Prevent logging from propagating to the root logger
            logger.propagate = 0

            formato = '[%(asctime)s].[{id:04d}] %(levelname)s - %(module)s:%(lineno)s: %(message)s'
            formato2 = '%H:%M:%S'

            basepath = RpiDns.get('folder.logs')

            if os.path.isdir(basepath) is False:
                os.mkdir(basepath)

            if basepath.endswith('/') is False:
                basepath += '/'

            carpeta_log = basepath

            if os.path.isdir(carpeta_log) is False:
                os.mkdir(carpeta_log)

            path = carpeta_log + hoy + '.log'

            Logger.CREATED = True

            if platform.system() == 'Windows':
                filename = None if windows_log != 'file' else path
            else:
                filename = None if linux_log != 'file' else path

            if os.path.isfile(filename) is False:
                with open(filename, 'wt', encoding='utf-8') as _:
                    pass

            with open(filename, encoding='utf-8') as fh:
                logs = fh.read()

            Logger.ID = max([int(x.group(1)) for x in re.finditer(r'\[\d{2}:\d{2}:\d{2}\].\[(\d+)\]', logs)]) + 1

            formatter = logging.Formatter(formato.format(**{'id': Logger.ID}), formato2)

            if platform.system() == 'Windows':
                if windows_log == 'file':
                    filehandler = logging.FileHandler(path, 'a', 'utf-8')
                    filehandler.setFormatter(formatter)
                    logger.addHandler(filehandler, )
                elif windows_log == 'console':
                    console = logging.StreamHandler()
                    console.setFormatter(formatter)
                    logger.addHandler(console)
                else:
                    raise WrongLogType(f"'{windows_log} no es un tipo válido de log ('file' | 'console')'")

            elif platform.system() == 'Linux':
                if windows_log == 'file':
                    filehandler = logging.FileHandler(path, 'a', 'utf-8')
                    filehandler.setFormatter(formatter)
                    logger.addHandler(filehandler)
                elif windows_log == 'console':
                    console = logging.StreamHandler()
                    console.setFormatter(formatter)
                    logger.addHandler(console)
                else:
                    raise WrongLogType(f"'{linux_log} no es un tipo válido de log ('file' | 'console')'")

            if platform.system() == 'Windows':
                logger.setLevel(windows_level)
                # logging.basicConfig(level=windows_level, format=formato, datefmt=formato2, filename=filename)
            else:
                logger.setLevel(linux_level)
                # logging.basicConfig(level=linux_level, format=formato, datefmt=formato2, filename=filename)

        return logger
