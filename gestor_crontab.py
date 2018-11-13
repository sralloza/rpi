# -*- coding: utf-8 -*-
import os
from difflib import SequenceMatcher
from enum import Enum

from crontab import CronTab

from rpi import plataforma
from .exceptions import UnrecognisedServiceError, JobNotFoundError, ExistingJobError


class CrontableService(object):
    def __init__(self, nombre, ruta):
        self.nombre = nombre
        self.ruta = ruta

    def __repr__(self):
        return f"{type(self).__name__}(nombre={self.nombre!r}, ruta={self.ruta!r})"


# class MenusService(AbstractCrontableService):
#     nombre = 'Menús Resi'
#     ruta = '/home/pi/scripts/menus_resi.py'


# class AemetService(AbstractCrontableService):
#     nombre = 'Aemet'
#     ruta = '/home/pi/scripts/aemet.py'


class CrontableServices(Enum):
    menus = CrontableService('Menús Resi', '/home/pi/scripts/menus_resi.py')
    aemet = CrontableService('Aemet', '/home/pi/scripts/aemet.py')

    @staticmethod
    def get_by_name(name):
        for elem in CrontableServices:
            if CrontableServices._similar(elem.name.lower(), name.lower()) > 0.7:
                return elem
            if CrontableServices._similar(elem.value.nombre.lower(), name.lower()) > 0.7:
                return elem

        raise UnrecognisedServiceError(f'Servicio no identificado: {name!r}')

    @staticmethod
    def _similar(a, b):
        return SequenceMatcher(None, a, b).ratio()


class GestorCrontab(object):
    BASE = '/usr/local/bin/python3 '

    def __init__(self):
        if plataforma() == 'W':
            self.cron = CronTab(tabfile='D:/PYTHON/raspberry_pi/rpi/crontab.txt')
        else:
            self.cron = CronTab(user=True)

    def nuevo(self, servicio, usuario, hora, minutos, *extra):
        servicio = CrontableServices.get_by_name(servicio).value
        command = GestorCrontab.BASE + servicio.ruta + ' ' + ' '.join(extra)
        for job in self.cron.find_comment(usuario.username):
            if command.strip() == job.command.strip() and hora == job.hour and minutos == job.minutes:
                raise ExistingJobError(f'Ya existe el trabajo: {job!r}')
        job = self.cron.new(command, comment=usuario.username)
        job.hour.on(hora)
        job.minutes.on(minutos)
        self.cron.write()

    def eliminar(self, servicio, usuario, hora, minutos):
        servicio_eliminar = CrontableServices.get_by_name(servicio).value
        jobs = self.cron.find_comment(usuario.username)
        select = None
        del servicio

        for job in jobs:
            servicio = CrontableServices.get_by_name(os.path.splitext(os.path.basename(job.command))[0]).value
            job_hora = int(str(job.hour))
            job_minutes = int(str(job.minutes))
            if job_hora == hora and job_minutes == minutos and servicio == servicio_eliminar:
                select = job
                self.cron.remove(job)

        if select is None:
            raise JobNotFoundError(
                f'No se encuentra el trabajo (username={usuario.username!r}, servicio={servicio_eliminar.nombre!r}, '
                f'hora={hora!r}, minutos={minutos!r})'
            )

        self.cron.write()

    def cambiar(self, servicio, usuario, hora_antigua, minutos_antiguos, hora_nueva, minutos_nuevos, *extra):
        servicio_original = servicio
        # servicio = CrontableServices.get_by_name(servicio).value
        # command = GestorCrontab.BASE + servicio.ruta + ' ' + ' '.join(extra)
        self.eliminar(usuario, servicio, hora_antigua, minutos_antiguos)

        self.nuevo(servicio_original, usuario, hora_nueva, minutos_nuevos, *extra)

    def listar_por_usuario(self, usuario):
        return list(self.cron.find_comment(usuario.username))


rpi_gct = GestorCrontab()
