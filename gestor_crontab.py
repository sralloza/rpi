# -*- coding: utf-8 -*-
from enum import Enum

from crontab import CronTab
from rpi import plataforma

from .exceptions import UnrecognisedServiceError


class AbstractCrontableService(object):
    nombre = None
    ruta = None

    def __repr__(self):
        return f"{type(self).__name__}(nombre={self.nombre!r}, ruta={self.ruta!r})"


class MenusService(AbstractCrontableService):
    nombre = 'Menús Resi'
    ruta = '/home/pi/scripts/menus_resi.py'


class AemetService(AbstractCrontableService):
    nombre = 'Aemet'
    ruta = '/home/pi/scripts/aemet.py'


class CrontableServices(Enum):
    menus = MenusService()
    aemet = AemetService()

    @staticmethod
    def get_by_name(name):
        for elem in CrontableServices:
            if elem.name == name:
                return elem

        raise UnrecognisedServiceError(f'Servicio no identificado: {name!r}')


class GestorCrontab(object):
    def __init__(self):
        if plataforma == 'W':
            self.cron = CronTab(tabfile='D:/PYTHON/raspberry_pi/crontab.txt')
        else:
            self.cron = CronTab(user='pi')

    # def


