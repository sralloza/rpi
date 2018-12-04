# -*- coding: utf-8 -*-

import json
import os
import sqlite3
from collections import namedtuple
from json import JSONDecodeError

from .gestor_crontab import GestorCrontab
from .gestor_servicios import GestorServicios, ServicioRaspberry
from rpi.dns import RpiDns
from rpi.exceptions import UnrecognisedUsernameError, InvalidLauncherError
from rpi.launcher import IftttLauncher, NotifyRunLauncher
from rpi.rpi_logging import Logger


class Usuario:
    """Representa un usuario."""

    def __init__(self, username, launcher, esta_activo, email, *servicios):
        self.username = username
        self.launcher = launcher
        self.cronitems = None
        self.esta_activo = bool(esta_activo)
        self.email = email

        if isinstance(servicios, str):
            self.servicios = (servicios,)
        else:
            if isinstance(servicios, tuple) and len(servicios) == 1:
                servicios = servicios[0]
                if isinstance(servicios, ServicioRaspberry):
                    self.servicios = (servicios,)
                else:
                    self.servicios = servicios

        self.actualizar_cronitems()

    def actualizar_cronitems(self):
        """Actualiza todas las tareas que ha creado el usuario."""
        self.cronitems = GestorCrontab().listar_por_usuario(self)

    def nuevo_proceso(self, servicio, hora, minutos, *extra):
        """Crea una nueva tarea."""
        GestorCrontab().nuevo(servicio, self, hora, minutos, *extra)
        self.actualizar_cronitems()

    def __repr__(self):
        return f"Usuario({self.username!r}, {self.launcher!r}, {self.servicios!r})"

    def __str__(self):
        return self.username


class GestorUsuarios(list):
    """Clase para gestionar los usuarios."""

    def __init__(self):
        super().__init__()
        self.path = None
        self.path2 = None

    def __str__(self):
        elems = [repr(e) for e in self]
        return '\n'.join(elems)

    @property
    def usernames(self):
        """Devuelve una tupla de los nombres de usuario."""
        return tuple([x.username for x in self])

    @property
    def emails(self):
        """Devuelve una tupla con todos los emails."""
        return tuple([x.email for x in self])

    @classmethod
    def load(cls):
        """Carga todos los usuarios."""
        self = cls.__new__(cls)
        self.__init__()
        TempUser = namedtuple('TempUser', ['username', 'launcher', 'esta_activo', 'email', 'servicios'])

        self.path = RpiDns.get('sqlite.django')

        if os.path.isfile(self.path) is False:
            logger = Logger.get(__file__, __name__)
            logger.critical('Archivo de usuarios no encontrado')
            raise FileNotFoundError('Archivo de usuarios no encontrado')

        self.con = sqlite3.connect(self.path)
        self.cur = self.con.cursor()
        self.cur.execute("select username, launcher, is_active, email, servicios from 'usuarios_usuario'")
        contenido = self.cur.fetchall()
        contenido = [TempUser(*x) for x in contenido]

        for user in contenido:
            username = user.username
            esta_activo = user.esta_activo
            email = user.email

            servicios = GestorServicios.evaluar(user.servicios)
            try:
                launcher = json.loads(user.launcher)
            except JSONDecodeError:
                continue

            if launcher["tipo"] == 'IFTTT':
                launcher = IftttLauncher(launcher["url"])
            elif launcher["tipo"] == "NotifyRun":
                launcher = NotifyRunLauncher(launcher["url"])
            else:
                raise InvalidLauncherError()

            self.append(Usuario(username, launcher, esta_activo, email, servicios))

        return self

    def get_by_username(self, username):
        """A partir de un nombre de usuario devuelve el usuario entero."""

        for usuario in self:
            if usuario.username == username:
                return usuario
        raise UnrecognisedUsernameError('Usuario no reconocido: ' + str(username))


rpi_gu = GestorUsuarios.load()
