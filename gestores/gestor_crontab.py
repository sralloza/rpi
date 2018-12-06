# -*- coding: utf-8 -*-

from crontab import CronTab, CronItem

from rpi import plataforma
from rpi.exceptions import JobNotFoundError, ExistingJobError, InvalidArgumentError
from .gestor_servicios import GestorServicios


class GestorCrontab(object):
    """Interfaz con crontab."""
    BASE = '/usr/local/bin/python3 '

    def __init__(self):
        if plataforma() == 'W':
            self.cron = CronTab(tabfile='D:/PYTHON/raspberry_pi/rpi/crontab.txt')
        else:
            self.cron = CronTab(user=True)

    def __iter__(self):
        return iter(self.cron)

    def nuevo(self, comando, usuario, hora, minutos):
        """Crea una nueva tarea en crontab."""

        try:
            username = usuario.username
        except AttributeError:
            username = usuario
        new_job = self.cron.new(comando, comment=username)
        new_job.hour.on(hora)
        new_job.minutes.on(minutos)

        contador = 0

        for job in self.cron.find_comment(username):
            if GestorCrontab.job_to_hash(job) == GestorCrontab.job_to_hash(new_job):
                contador += 1

        if contador > 1:
            raise ExistingJobError(f'Ya existe el trabajo: {new_job!r}')
        self.cron.write()

    def eliminar(self, anything):
        """Alias para GestorCrontab.eliminar_por_hash()."""

        if isinstance(anything, CronItem):
            hashcode = GestorCrontab.job_to_hash(anything)
        elif isinstance(anything, int):
            hashcode = anything
        elif isinstance(anything, str):
            hashcode = int(anything)
        else:
            raise InvalidArgumentError(f'Tipo incorrecto ({type(anything).__name__!r})')
        return self.eliminar_por_hash(hashcode)

    def eliminar_por_hash(self, hashcode):
        """Elimina una tarea a partir de su hash generado por GestorCrontab.job_to_hash()."""

        select = None
        jobs = list(self.cron)

        for job in jobs:
            if self.job_to_hash(job) == hashcode:
                select = job
                self.cron.remove(job)

        if select is None:
            raise JobNotFoundError(
                f'No se encuentra el trabajo (hash={hashcode!r})'
            )

        self.cron.write()

    def listar_por_usuario(self, usuario):
        """Devuelve una lista con todas las tareas de un usuario"""

        try:
            username = usuario.username
        except AttributeError:
            username = usuario

        return list(self.cron.find_comment(username))

    @staticmethod
    def job_to_hash(job: CronItem):
        """Devuelve un valor hash a partir de una tarea"""

        return hash(str(vars(job)))
