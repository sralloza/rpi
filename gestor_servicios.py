import os
from enum import Enum
from warnings import warn

from rpi.exceptions import UnrecognisedServiceWarning, UnexpectedBehaviourWarning, InvalidArgumentError


class ServicioRaspberry(object):
    def __init__(self, name, basename, argumentos, configuracion=None, ispublic=False):
        if configuracion is None:
            configuracion = ()

        self.name = name

        if isinstance(basename, str):
            basename = (basename,)
        try:
            self.basename = tuple(basename)
        except TypeError:
            raise InvalidArgumentError(f'Invalid type ({type(basename).__name__})')

        if isinstance(configuracion, str):
            configuracion = (configuracion,)
        try:
            self.configuracion = tuple(configuracion)
        except TypeError:
            raise InvalidArgumentError(f'Invalid type ({type(configuracion).__name__})')

        self.configuracion = configuracion
        self.argumentos = argumentos
        self.ispublic = ispublic

    def isfile(self, other):
        return self.ispath(other)

    def ispath(self, other):
        return other in self.basename

    def __repr__(self):
        return f"ServicioRaspberry({self.name})"


class GestorServicios(Enum):
    """Clase que representa los servicios que se ejecutan en la rpi."""
    AEMET = ServicioRaspberry('AEMET', 'aemet.py', ['hoy', 'manana', 'pasado', 'todos'], ispublic=True)
    MENUS = ServicioRaspberry('MENUS', 'menus_resi.py', ['comida', 'cena', 'default'], ispublic=True)

    VCS = ServicioRaspberry('VCS', 'vcs.py', [], configuracion=['campus_username', 'campus_password'], ispublic=True)
    ENVIAR = ServicioRaspberry('ENVIAR', 'enviar.py', [])

    LOG = ServicioRaspberry('LOG', '', [])

    UNKOWN = ServicioRaspberry('UNKOWN', '?', [])

    def __repr__(self):
        return self.__class__.__name__ + '.' + self.name

    def __str__(self):
        return self.name

    @staticmethod
    def get(path):
        """A partir de la ruta de un archivo, esta función determina su servicio y lo devuelve. Si no lo encuentra,
        lanza ValueError."""

        path = os.path.basename(path)
        for servicio in GestorServicios:
            if servicio.value.isfile(path):
                return servicio.value
        else:
            if path in (
                    'backup.py', 'ngrok.py', 'ngrok2.py', 'reboot.py',
                    'serveo.py', 'gestor_mail.py', 'controller.py', 'pull.sh'):
                return GestorServicios.LOG.value
            warn(f"Servicio no reconocido: {path}", UnrecognisedServiceWarning)
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
