# -*- coding: utf-8 -*-

import datetime
import io
import logging
import os
import platform
import sys
import traceback

from .dns import RpiDns
from .exceptions import WrongCalledError

# Copied from logging.__init__.py
if hasattr(sys, '_getframe'):
    # noinspection PyProtectedMember
    def currentframe():
        return sys._getframe(3)
else:
    # noinspection PyBroadException
    def currentframe():
        try:
            raise Exception
        except Exception:
            return sys.exc_info()[2].tb_frame.f_back

_srcfile = __file__.lower()


class RpiLogger(logging.Logger):
    def __init__(self, name):
        super().__init__(name)

    def findCaller(self, stack_info=False):
        """Copied from logging.__init__.py."""

        f = currentframe()

        if f is not None:
            f = f.f_back
        rv = "(unknown file)", 0, "(unknown function)", None
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            if filename == _srcfile:
                f = f.f_back
                continue
            sinfo = None
            if stack_info:
                sio = io.StringIO()
                sio.write('Stack (most recent call last):\n')
                traceback.print_stack(f, file=sio)
                sinfo = sio.getvalue()
                if sinfo[-1] == '\n':
                    sinfo = sinfo[:-1]
                sio.close()
            rv = (co.co_filename, f.f_lineno, co.co_name, sinfo)
            break
        return rv

    def log(self, level, msg, *args, enable=True, **kwargs):

        if not isinstance(level, int):
            raise TypeError("level must be an integer")
        if self.isEnabledFor(level) and enable is True:
            self._log(level, msg, args, **kwargs)

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False):
        """Copied from logging.__init__.py."""

        sinfo = None
        if _srcfile:

            try:
                fn, lno, func, sinfo = self.findCaller(stack_info)
            except ValueError:
                fn, lno, func = "(unknown file)", 0, "(unknown function)"
        else:
            fn, lno, func = "(unknown file)", 0, "(unknown function)"
        if exc_info:
            if isinstance(exc_info, BaseException):
                exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
            elif not isinstance(exc_info, tuple):
                exc_info = sys.exc_info()
        record = self.makeRecord(self.name, level, fn, lno, msg, args,
                                 exc_info, func, extra, sinfo)
        self.handle(record)

    def info(self, msg, *args, enable=True, **kwargs):
        if self.isEnabledFor(logging.INFO):
            self.log(logging.INFO, msg, *args, enable=enable, **kwargs)

    def debug(self, msg, *args, enable=True, **kwargs):
        if self.isEnabledFor(logging.DEBUG):
            self.log(logging.DEBUG, msg, *args, enable=enable, **kwargs)

    def warning(self, msg, *args, enable=True, **kwargs):
        if self.isEnabledFor(logging.WARNING):
            self.log(logging.WARNING, msg, *args, enable=enable, **kwargs)

    def error(self, msg, *args, enable=True, **kwargs):
        if self.isEnabledFor(logging.ERROR):
            self.log(logging.ERROR, msg, *args, enable=enable, **kwargs)

    def critical(self, msg, *args, enable=True, **kwargs):
        if self.isEnabledFor(logging.CRITICAL):
            self.log(logging.CRITICAL, msg, *args, enable=enable, **kwargs)


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
