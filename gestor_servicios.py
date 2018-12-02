import os
from enum import Enum
from typing import List
from warnings import warn

from rpi.exceptions import UnrecognisedServiceWarning, UnexpectedBehaviourWarning, InvalidArgumentError


class Opcion(object):
    def __init__(self, nombre, tipo, incluir=True):
        self.nombre = nombre
        self.tipo = tipo
        self.incluir = incluir


class Comando(object):

    def __init__(self, plantilla, ruta, notificar=True, preopcion=''):
        self.preopcion = preopcion
        self.ruta = ruta

        if notificar is True:
            if plantilla.endswith(' ') is False:
                plantilla += ' '
            plantilla += '-notificar {USUARIO}'

        self.plantilla = plantilla

    def __format__(self, **kwargs):
        assert isinstance(kwargs['OPCIONES'], (tuple, list))
        kwargs['OPCIONES'] = ' '.join([self.preopcion + x for x in kwargs['OPCIONES']])
        return self.plantilla.format(**kwargs)

    def format(self, **kwargs):
        return self.__format__(**kwargs)


class ServicioRaspberry(object):
    DEFAULT = {'PYTHON': '/usr/local/bin/python3'}

    def __init__(self, nombre, comando, opciones: List[Opcion] = None, ruta='', rutas_extra=None, datos=None,
                 esabstracto=False, espublico=False):
        if datos is None:
            datos = ()

        self.nombre = nombre
        self.comando = comando
        self.opciones = opciones if opciones is not None else list()
        self.ruta = ruta
        self.esabstracto = esabstracto

        rutas_extra = rutas_extra if rutas_extra is not None else tuple()

        if isinstance(rutas_extra, str):
            rutas_extra = (rutas_extra,)
        try:
            self.rutas_extra = tuple(rutas_extra)
        except TypeError:
            raise InvalidArgumentError(f'Invalid type ({type(rutas_extra).__nombre__})')

        self.basenombres = tuple([os.path.basename(x).lower() for x in self.rutas_extra])

        if isinstance(datos, str):
            datos = (datos,)
        try:
            self.datos = tuple(datos)
        except TypeError:
            raise InvalidArgumentError(f'Invalid type ({type(datos).__nombre__})')

        self.datos = datos
        self.espublico = espublico
        self.nombres = [os.path.splitext(x)[0].lower() for x in self.basenombres]

    def __repr__(self):
        return f"ServicioRaspberry({self.nombre})"

    @property
    def nombres_opciones(self):
        return [x.nombre for x in self.opciones]

    def isfile(self, other):
        return self.ispath(other)

    def ispath(self, other):
        other = os.path.basename(other).lower()
        condition = other in self.basenombres

        if condition is False:
            return other in self.nombres
        return condition

    def generar_comando(self, **kwargs):
        kwargs.update(**ServicioRaspberry.DEFAULT)
        kwargs.update(RUTA=self.ruta)

        if 'opciones' in kwargs:
            kwargs['OPCIONES'] = kwargs['opciones']
            del kwargs['opciones']
        if 'usuario' in kwargs:
            kwargs['USUARIO'] = kwargs['usuario']
            del kwargs['usuario']

        try:
            for opt in kwargs['OPCIONES']:
                if opt not in self.nombres_opciones:
                    raise RuntimeError
        except KeyError:
            raise RuntimeError

        return self.comando.format(**kwargs)


class GestorServicios(Enum):
    """Clase que representa los servicios que se ejecutan en la rpi."""
    AEMET = ServicioRaspberry(
        nombre='AEMET',
        comando=Comando(
            plantilla='{PYTHON} {RUTA} {OPCIONES}',
            ruta='/home/pi/scripts/aemet.py',
            preopcion='-',
        ),
        opciones=[
            Opcion('hora', 'time', incluir=False),
            Opcion('hoy', 'radio'),
            Opcion('manana', 'radio'),
            Opcion('pasado', 'radio'),
            Opcion('todos', 'radio')
        ],
        ruta='/home/pi/scripts/aemet.py',
        espublico=True,
    )
    MENUS = ServicioRaspberry(
        nombre='MENUS',
        comando=Comando(
            plantilla='{PYTHON} {RUTA} salida -mostrar {OPCIONES}',
            ruta='/home/pi/scripts/menus_resi.py',
        ),
        opciones=[
            Opcion('hora', 'time', incluir=False),
            Opcion('comida', 'radio'),
            Opcion('cena', 'radio'),
            Opcion('default', 'radio')
        ],
        ruta='/home/pi/scripts/menus_resi.py',
        espublico=True,
    )

    VCS = ServicioRaspberry(
        nombre='VCS',
        comando=Comando(
            # todo: crear comando
            plantilla='{PYTHON} {RUTA} {OPCIONES}',
            ruta='/home/pi/scripts/vcs.py',
        ),
        opciones=[
            Opcion('fecha', 'time', incluir=False),
        ],
        ruta='/home/pi/scripts/vcs.py',
        datos=['campus_username', 'campus_password'],
        espublico=True
    )
    ENVIAR = ServicioRaspberry(
        nombre='ENVIAR',
        comando=Comando(
            plantilla='{PYTHON} {RUTA} {OPCIONES}',
            ruta='/home/pi/scripts/enviar.py',
        ),
        opciones=[],
        ruta='/home/pi/scripts/enviar.py',
    )

    LOG = ServicioRaspberry(
        nombre='LOG',
        comando=Comando(
            plantilla=None,
            ruta=None,
            notificar=False,
        ),
        opciones=[],
        rutas_extra=[
            '/home/pi/scripts/backup.py', '/home/pi/scripts/ngrok.py', '/home/pi/scripts/ngrok2.py',
            '/home/pi/scripts/reboot.py', '/home/pi/scripts/serveo.py', '/home/pi/scripts/gestor_mail.py',
            '/home/pi/scripts/controller.py', '/home/pi/pull.sh'
        ],
        esabstracto=True
    )

    UNKNOWN = ServicioRaspberry(
        nombre='UNKOWN',
        comando=Comando(
            plantilla=None,
            ruta=None,
            notificar=False,
        ),
        opciones=[],
        esabstracto=True
    )

    def __repr__(self):
        return self.__class__.__nombre__ + '.' + self.nombre

    def __str__(self):
        return self.nombre

    @staticmethod
    def get(basepath):

        if isinstance(basepath, ServicioRaspberry):
            return basepath
        if isinstance(basepath, GestorServicios):
            return basepath.value

        basepath = os.path.basename(basepath).lower()
        for servicio in GestorServicios:
            if servicio.nombre.lower() == basepath:
                return servicio.value
            if servicio.value.isfile(basepath):
                return servicio.value

        warn(f"Servicio no reconocido: {basepath}", UnrecognisedServiceWarning)
        return GestorServicios.UNKNOWN.value

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
