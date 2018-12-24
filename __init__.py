# -*- coding: utf-8 -*-

import platform

# __VERSION__ = '2018.11.15'

__VERSION__ = 'new_services-alfa-1.01'
ADMIN_EMAIL = 'sralloza@gmail.com'


def operating_system():
    """Returns L if linux and W if windows."""
    return platform.system()[0]


def opating_system_in_brackets():
    """Returns the operating system icon between brakets."""
    return '(' + operating_system() + ')'
