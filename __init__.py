# -*- coding: utf-8 -*-

import platform

# __VERSION__ = '2018.11.15'

__VERSION__ = 'new_services-alfa-0.47'
ADMIN_EMAIL = 'sralloza@gmail.com'


def operating_system():
    """Returns L if linux and W if windows."""
    return platform.system()[0]


def opating_system_in_brackets():
    """Devuelve '(W)' si se ejecuta en windows, o '(L)' si se ejecuta en Linux."""
    return '(' + operating_system() + ')'
