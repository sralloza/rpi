# -*- coding: utf-8 -*-

import json
import os
from enum import Enum
from json import JSONDecodeError

from rpi.gestor_crontab import rpi_gct
from .dns import RpiDns
from .exceptions import UnrecognisedUsernameError, UnrecognisedServiceError, InvalidLauncherError, AuxiliarFileError
from .launcher import IftttLauncher, NotifyRunLauncher
from .rpi_logging import Logger


class Servicios(Enum):
    """Clase que representa los servicios que se ejecutan en la rpi."""
    MENUS = 'menus_resi.py'
    VCS = 'vcs.py'
    ENVIAR = 'enviar.py'
    AEMET = 'aemet.py'
    LOG = 0

    def __repr__(self):
        return self.__class__.__name__ + '.' + self.name

    def __str__(self):
        return self.name

    @staticmethod
    def get(path):
        """A partir de la ruta de un archivo, esta función determina su servicio y lo devuelve. Si no lo encuentra,
        lanza ValueError."""

        path = os.path.basename(path)
        for servicio in Servicios:
            if servicio.value == path:
                return servicio
        else:
            if path in (
                    'backup.py', 'ngrok.py', 'ngrok2.py', 'reboot.py',
                    'serveo.py', 'gestor_mail.py', 'controller.py', 'pull.sh'):
                return Servicios.LOG
            raise UnrecognisedServiceError(f"Servicio no reconocido: {path}")

    @staticmethod
    def evaluar(algo):
        """Hace la conversión str -> Servicios."""
        return eval(algo, globals(), Servicios.__dict__)


class Usuario:
    """Representa un usuario afiliado a un servicio."""

    def __init__(self, username, launcher, *servicios, signed_up=None, password=None):
        self.username = username
        self.launcher = launcher
        self.signed_up = signed_up
        self.password = password
        self.cronitems = None

        if isinstance(servicios, str):
            self.servicios = (servicios,)
        else:
            if isinstance(servicios, tuple) and len(servicios) == 1:
                servicios = servicios[0]
                if isinstance(servicios, Servicios):
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
        return f"Usuario({self.username!r}, {self.launcher!r}, {self.servicios!r}, {self.signed_up!r})"

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
        return cls.from_json()

    @classmethod
    def from_json(cls):
        """Carga todos los usuarios."""
        self = cls.__new__(cls)
        self.__init__()

        self.path = RpiDns.get('json.usuarios')
        self.path2 = self.path.replace('usuarios', 'usuarios_web')

        if os.path.isfile(self.path) is False:
            logger = Logger.get(__file__, __name__)
            logger.critical('Archivo de usuarios no encontrado')
            raise FileNotFoundError('Archivo de usuarios no encontrado')

        with open(self.path) as f:
            contenido = json.load(f)

        try:
            with open(self.path2) as f:
                contenido += json.load(f)
        except (FileNotFoundError, JSONDecodeError):
            pass

        for user in contenido:
            username = user['username']

            if username in self.usernames:
                continue

            servicios = Servicios.evaluar(user['servicios'])
            launcher = user['launcher']
            signed_up = user.get('signed-up')
            password = user.get('password')

            if launcher["tipo"] == 'IFTTT':
                launcher = IftttLauncher(launcher["url"])
            elif launcher["tipo"] == "NotifyRun":
                launcher = NotifyRunLauncher(launcher["url"])
            else:
                raise InvalidLauncherError()

            self.append(Usuario(username, launcher, servicios, signed_up=signed_up, password=password))

        self.save()

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
        try:
            with open(self.path2, 'wt') as f:
                f.write('')
        except FileNotFoundError:
            pass
        with open(self.path, 'w') as f:
            json.dump(self.to_json, f, indent=4, sort_keys=True)

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
