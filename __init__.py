# -*- coding: utf-8 -*-

import platform

# __VERSION__ = '2018.11.15'

__VERSION__ = 'new_services-alfa-0.26'
ADMIN_EMAIL = 'sralloza@gmail.com'


def plataforma():
    """Devuelve L si se ejecuta en Linux y W si se ejecuta en Windows."""
    return platform.system()[0]


def info_plataforma():
    """Devuelve '(W)' si se ejecuta en windows, o '(L)' si se ejecuta en Linux."""
    return '(' + plataforma() + ')'
