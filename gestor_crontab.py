# -*- coding: utf-8 -*-

import os

from crontab import CronTab

from rpi import plataforma
from rpi.gestor_servicios import GestorServicios
from .exceptions import JobNotFoundError, ExistingJobError


class CrontableService(object):
    def __init__(self, nombre, ruta):
        self.nombre = nombre
        self.ruta = ruta

    def __repr__(self):
        return f"{type(self).__name__}(nombre={self.nombre!r}, ruta={self.ruta!r})"


class GestorCrontab(object):
    BASE = '/usr/local/bin/python3 '

    def __init__(self):
        if plataforma() == 'W':
            self.cron = CronTab(tabfile='D:/PYTHON/raspberry_pi/rpi/crontab.txt')
        else:
            self.cron = CronTab(user=True)

    def nuevo(self, servicio, usuario, hora, minutos, *extra):
        servicio = GestorServicios.get(servicio)
        command = GestorCrontab.BASE + servicio.ruta + ' ' + ' '.join(extra)

        new_job = self.cron.new(command, comment=usuario.username)
        new_job.hour.on(hora)
        new_job.minutes.on(minutos)

        contador = 0

        for job in self.cron.find_comment(usuario.username):
            # if command.strip() == job.command.strip() and hora == job.hour and minutos == job.minutes:
            if new_job.command == job.command and new_job.hour == job.hour and new_job.minutes == job.minutes:
                contador += 1

        if contador > 1:
            raise ExistingJobError(f'Ya existe el trabajo: {job!r}')
        self.cron.write()

    def eliminar(self, servicio, usuario, hora, minutos):
        servicio_eliminar = GestorServicios.get(servicio)
        jobs = self.cron.find_comment(usuario.username)
        select = None
        del servicio

        for job in jobs:
            servicio = GestorServicios.get(os.path.splitext(os.path.basename(job.command))[0])
            job_hora = int(str(job.hour))
            job_minutes = int(str(job.minutes))
            if job_hora == hora and job_minutes == minutos and servicio == servicio_eliminar:
                select = job
                self.cron.remove(job)

        if select is None:
            raise JobNotFoundError(
                f'No se encuentra el trabajo (username={usuario.username!r}, servicio={servicio_eliminar.name!r}, '
                f'hora={hora!r}, minutos={minutos!r})'
            )

        self.cron.write()

    def cambiar(self, servicio, usuario, hora_antigua, minutos_antiguos, hora_nueva, minutos_nuevos, *extra):
        servicio_original = servicio
        # servicio = CrontableServices.get_by_name(servicio).value
        # command = GestorCrontab.BASE + servicio.ruta + ' ' + ' '.join(extra)
        self.eliminar(usuario, servicio, hora_antigua, minutos_antiguos, *extra)

        self.nuevo(servicio_original, usuario, hora_nueva, minutos_nuevos, *extra)

    def listar_por_usuario(self, usuario):
        return list(self.cron.find_comment(usuario.username))


rpi_gct = GestorCrontab()
