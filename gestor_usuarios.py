# -*- coding: utf-8 -*-

import json
import os
import sqlite3
from collections import namedtuple
from json import JSONDecodeError

from rpi.gestor_crontab import rpi_gct
from rpi.gestor_servicios import GestorServicios, ServicioRaspberry
from .dns import RpiDns
from .exceptions import UnrecognisedUsernameError, InvalidLauncherError, AuxiliarFileError, \
    UnableToSave
from .launcher import IftttLauncher, NotifyRunLauncher
from .rpi_logging import Logger


class Usuario:
    """Representa un usuario afiliado a un servicio."""

    def __init__(self, username, launcher, esta_activo, *servicios):
        self.username = username
        self.launcher = launcher
        self.cronitems = None
        self.esta_activo = bool(esta_activo)

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
        self.cronitems = rpi_gct.listar_por_usuario(self)

    def nuevo_proceso(self, servicio, hora, minutos, *extra):
        rpi_gct.nuevo(servicio, self, hora, minutos, *extra)
        self.actualizar_cronitems()

    def cambiar_proceso(self, servicio, hora_antigua, hora_nueva, minutos_antiguos, minutos_nuevos, *extra):
        rpi_gct.cambiar(servicio, self, hora_antigua, hora_nueva, minutos_antiguos, minutos_nuevos, *extra)

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

    @classmethod
    def load(cls):
        """Carga todos los usuarios."""
        self = cls.__new__(cls)
        self.__init__()
        TempUser = namedtuple('TempUser', ['username', 'launcher', 'esta_activo', 'servicios'])

        self.path = RpiDns.get('sqlite.django')

        if os.path.isfile(self.path) is False:
            logger = Logger.get(__file__, __name__)
            logger.critical('Archivo de usuarios no encontrado')
            raise FileNotFoundError('Archivo de usuarios no encontrado')

        self.con = sqlite3.connect(self.path)
        self.cur = self.con.cursor()
        self.cur.execute("select username, launcher, is_active, servicios from 'usuarios_usuario'")
        contenido = self.cur.fetchall()
        contenido = [TempUser(*x) for x in contenido]

        for user in contenido:
            username = user.username
            esta_activo = user.esta_activo

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

            self.append(Usuario(username, launcher, esta_activo, servicios))

        return self

    @property
    def to_json(self):
        foo = []
        for user in self:
            bar = dict()
            bar["username"] = user.username
            bar["password"] = user.password
            bar["servicios"] = ', '.join([str(x) for x in user.servicios])
            bar["launcher"] = user.launcher.to_json()
            foo.append(bar)

        return foo

    def delete(self, username):

        if isinstance(username, Usuario) is True:
            self.remove(username)
        else:
            self.remove(self.get_by_username(username))

    def save(self):
        raise UnableToSave('Usa la página web')

    def get_by_username(self, username):
        """A partir de un nombre de usuario devuelve el usuario entero

        :param str username: nombre del usuario a buscar.
        :rtype: Usuario
        :raises UnrecognisedUsernameError: si el usuario no se encuentra.
        """

        for usuario in self:
            if usuario.username == username:
                return usuario
        raise UnrecognisedUsernameError('Usuario no reconocido: ' + str(username))


rpi_gu = GestorUsuarios.load()

if __name__ == '__main__':
    raise AuxiliarFileError('Es un archivo auxiliar')
