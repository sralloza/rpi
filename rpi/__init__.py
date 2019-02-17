# -*- coding: utf-8 -*-

"""Module made to automate tasks of the raspberry pi."""

import platform

# __VERSION__ = '2018.11.15'

__VERSION__ = '2019.2.17'
ADMIN_EMAIL = 'sralloza@gmail.com'


def operating_system():
    """Returns L if linux and W if windows."""
    return platform.system()[0]


def operating_system_in_brackets():
    """Returns the operating system icon between brakets."""
    return '(' + operating_system() + ')'
