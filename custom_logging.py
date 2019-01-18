"""Logging configuration for the rest of scripts."""

import datetime
import logging
import os

from rpi.dns import RpiDns


class LoggingInfo(object):
    """Abstract class to store logs folders and file paths."""

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
    LOGS_DAY_FOLDER = os.path.join(LOGS_MONTH_FOLDER, str(today.day))

    LOGS_APACHE_ACCESS = '/var/log/apache2/access.log'
    LOGS_APACHE_ERRROR = '/var/log/apache2/error.log'

    if os.path.isdir(LOGS_GENERAL_FOLDER) is False:
        os.mkdir(LOGS_GENERAL_FOLDER)

    if os.path.isdir(LOGS_YEAR_FOLDER) is False:
        os.mkdir(LOGS_YEAR_FOLDER)

    if os.path.isdir(LOGS_MONTH_FOLDER) is False:
        os.mkdir(LOGS_MONTH_FOLDER)

    if os.path.isdir(LOGS_DAY_FOLDER) is False:
        os.mkdir(LOGS_DAY_FOLDER)


def get_dict_config(filename=None, called_from=None, name=None, use_logs_folder=False):
    """

    Args:
        filename (str): filename path, exact filename.
        called_from (str): path of the script that requests the logger. The name of the logger will
            be the name of that file, without extension and path.
        name (str): name of the file. The filename will be ```name``` + .txt
        use_logs_folder (bool): decide to use or not the logs folder.

    Returns:
        dict: logging config.

    """
    if called_from:
        filename = os.path.split(os.path.splitext(called_from)[0])[1] + '.log'
    elif not filename:
        filename = name + '.log'

    if use_logs_folder:
        filename = os.path.join(LoggingInfo.LOGS_DAY_FOLDER, filename)

    dict_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '[%(levelname)s] %(name)s: %(message)s'
            },
            'advanced': {
                'format': '[%(asctime)s] %(levelname)-8s - %(name)s:%(lineno)s: %(message)s'
            }
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
            },
            'file': {
                'level': 'DEBUG',
                'formatter': 'advanced',
                'class': 'logging.FileHandler',
                'filename': filename
            },
        },
        'loggers': {
            '': {
                'handlers': ['file'],
                'level': 'DEBUG',
                'propagate': True
            },
        }
    }

    return dict_config
