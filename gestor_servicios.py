import os
from collections import namedtuple
from enum import Enum
from warnings import warn

from rpi.exceptions import UnrecognisedServiceWarning, UnexpectedBehaviourWarning, InvalidArgumentError

ArgumentoServicioRaspberry = namedtuple('ArgumentoServicioRaspberry', ['nombre', 'tipo'])


class ServicioRaspberry(object):
    def __init__(self, name, paths, argumentos, datos=None, ispublic=False):
        if datos is None:
            datos = ()

        self.name = name

        if isinstance(paths, str):
            paths = (paths,)
        try:
            self.paths = tuple(paths)
        except TypeError:
            raise InvalidArgumentError(f'Invalid type ({type(paths).__name__})')

        self.basenames = tuple([os.path.basename(x).lower() for x in self.paths])

        if isinstance(datos, str):
            datos = (datos,)
        try:
            self.datos = tuple(datos)
        except TypeError:
            raise InvalidArgumentError(f'Invalid type ({type(datos).__name__})')

        self.datos = datos
        self.argumentos = argumentos
        self.ispublic = ispublic
        self.names = [os.path.splitext(x)[0].lower() for x in self.basenames]

    def __repr__(self):
        return f"ServicioRaspberry({self.name})"

    @property
    def ruta(self):
        return self.paths[0]

    def isfile(self, other):
        return self.ispath(other)

    def ispath(self, other):
        other = os.path.basename(other).lower()
        condition = other in self.basenames

        if condition is False:
            return other in self.names
        return condition


class GestorServicios(Enum):
    """Clase que representa los servicios que se ejecutan en la rpi."""
    AEMET = ServicioRaspberry('AEMET', '/home/pi/scripts/aemet.py', [
        ArgumentoServicioRaspberry('fecha', 'time'),
        ArgumentoServicioRaspberry('hoy', 'radio'),
        ArgumentoServicioRaspberry('manana', 'radio'),
        ArgumentoServicioRaspberry('pasado', 'radio'),
        ArgumentoServicioRaspberry('todos', 'radio')
    ], ispublic=True)
    MENUS = ServicioRaspberry('MENUS', '/home/pi/scripts/menus_resi.py', [
        ArgumentoServicioRaspberry('comida', 'radio'),
        ArgumentoServicioRaspberry('cena', 'radio'),
        ArgumentoServicioRaspberry('default', 'radio')
    ], ispublic=True)

    VCS = ServicioRaspberry('VCS', '/home/pi/scripts/vcs.py', [], datos=['campus_username', 'campus_password'])
    ENVIAR = ServicioRaspberry('ENVIAR', '/home/pi/scripts/enviar.py', [])

    LOG = ServicioRaspberry('LOG', [
        '/home/pi/scripts/backup.py', '/home/pi/scripts/ngrok.py', '/home/pi/scripts/ngrok2.py',
        '/home/pi/scripts/reboot.py', '/home/pi/scripts/serveo.py', '/home/pi/scripts/gestor_mail.py',
        '/home/pi/scripts/controller.py', '/home/pi/pull.sh'
    ], [])

    UNKOWN = ServicioRaspberry('UNKOWN', '?', [])

    def __repr__(self):
        return self.__class__.__name__ + '.' + self.name

    def __str__(self):
        return self.name

    @staticmethod
    def get(basepath):

        if isinstance(basepath, ServicioRaspberry):
            return basepath
        if isinstance(basepath, GestorServicios):
            return basepath.value

        basepath = os.path.basename(basepath)
        for servicio in GestorServicios:
            if servicio.value.isfile(basepath):
                return servicio.value

        warn(f"Servicio no reconocido: {basepath}", UnrecognisedServiceWarning)
        return GestorServicios.UNKOWN.value

    @staticmethod
    def evaluar(algo):
        """Hace la conversión str -> Servicios."""
        try:
            data = eval(algo, globals(), GestorServicios.__dict__)
        except SyntaxError:
            return tuple()

        try:
            data = list(data)
        except TypeError:
            data = [data, ]

        for i in range(len(data)):
            try:
                data[i] = data[i].value
            except AttributeError:
                warn(f"Puede que algo haya ido mal (data={data})", UnexpectedBehaviourWarning)

        return tuple(data)
