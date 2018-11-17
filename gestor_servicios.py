import os
from enum import Enum

from rpi.exceptions import UnrecognisedServiceError


class ServicioRaspberry(object):
    def __init__(self, name, basename, options):
        self.name = name
        self.basename = basename
        self.options = options


class GestorServicios(Enum):
    """Clase que representa los servicios que se ejecutan en la rpi."""
    MENUS = ServicioRaspberry('MENUS', 'menus_resi.py', ['comida', 'cena', 'default'])
    VCS = ServicioRaspberry('VCS', 'vcs.py', ['campus_username', 'campus_password'])
    ENVIAR = ServicioRaspberry('ENVIAR', 'enviar.py', [])
    AEMET = ServicioRaspberry('AEMET', 'aemet.py', ['hoy', 'manana', 'pasado', 'todos'])
    UNKOWN = ServicioRaspberry('UNKOWN', '?', [])
    LOG = ServicioRaspberry('LOG', 0, [])

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
            if servicio.value == path:
                return servicio
        else:
            if path in (
                    'backup.py', 'ngrok.py', 'ngrok2.py', 'reboot.py',
                    'serveo.py', 'gestor_mail.py', 'controller.py', 'pull.sh'):
                return GestorServicios.LOG
            raise UnrecognisedServiceError(f"Servicio no reconocido: {path}")

    @staticmethod
    def evaluar(algo):
        """Hace la conversión str -> Servicios."""
        try:
            return eval(algo, globals(), GestorServicios.__dict__)
        except SyntaxError:
            return []
