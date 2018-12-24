import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple, Union
from warnings import warn

from rpi.exceptions import UnrecognisedServiceWarning, UnexpectedBehaviourWarning, MissingOptionsError, \
    InvalidOptionError


class Option(object):
    def __init__(self, name, type, include=True):
        self.name = name
        self.type = type
        self.include = include


class Command(object):

    def __init__(self, template, path, notify=True, preoption=''):
        self.preoption = preoption
        self.path = path

        if notify is True:
            if template.endswith(' ') is False:
                template += ' '
            template += '-notify {USERNAME}'

        self.template = template

    def __format__(self, **kwargs):
        assert isinstance(kwargs['OPTIONS'], (tuple, list))
        kwargs['OPTIONS'] = ' '.join([self.preoption + x for x in kwargs['OPTIONS']])
        return self.template.format(**kwargs)

    def format(self, **kwargs):
        return self.__format__(**kwargs)


@dataclass(repr=False)
class RaspberryService(object):
    DEFAULT = {'PYTHON': '/usr/local/bin/python3'}
    name: str
    command: Command
    options: Union[Tuple[Option], tuple] = None
    path: str = ''
    extra_paths: tuple = None
    data: tuple = None
    isabstract: bool = False
    ispublic: bool = False

    all_paths: tuple = field(init=False)

    def __post_init__(self):

        if self.extra_paths is None:
            self.extra_paths = tuple()

        try:
            self.extra_paths = tuple(self.extra_paths)
        except TypeError:
            raise TypeError(f'Invalid type ({self.extra_paths.__class__.__name__})')

        if self.data is None:
            self.data = ()

        if self.options is None:
            self.options = tuple()

        self.all_paths = self.extra_paths + (self.path,)

    def __repr__(self):
        return f"RaspberryService({self.name})"

    @property
    def options_names(self):
        return [x.name for x in self.options]

    @property
    def filenames_with_ext(self):
        """list of filenames with extension (enviar.py, aemet.py, ...)."""
        return tuple([os.path.basename(x).lower() for x in self.all_paths])

    @property
    def filenames_without_ext(self):
        """list of filenames without extension (enviar, aemet, ...)."""
        return [os.path.splitext(x)[0].lower() for x in self.filenames_with_ext]

    def corresponds_with(self, other):
        other = os.path.basename(other).lower()

        if other == self.name.lower():
            return True

        if other in self.filenames_with_ext:
            return True

        if other in self.filenames_without_ext:
            return True

        return False

    def generate_command(self, **kwargs):
        kwargs.update(**RaspberryService.DEFAULT)
        kwargs.update(RUTA=self.path)

        if 'options' in kwargs:
            kwargs['OPTIONS'] = kwargs['options']
            del kwargs['options']

        if 'username' in kwargs:
            kwargs['USERNAME'] = kwargs['username']
            del kwargs['username']

        try:
            for opt in kwargs['OPTIONS']:
                if opt not in self.options_names:
                    raise InvalidOptionError(f'Option {opt!r} is not registered ({self.options_names!r})')
        except KeyError:
            raise MissingOptionsError('Options have not been specified')

        return self.command.format(**kwargs)


class ServiceManager(Enum):
    """Manager for the raspberry services."""

    AEMET = RaspberryService(
        name='AEMET',
        command=Command(
            template='{PYTHON} {PATH} {OPTIONS}',
            path='/home/pi/scripts/aemet.py',
            preoption='-',
        ),
        options=(
            Option('hora', 'time', include=False),
            Option('hoy', 'radio'),
            Option('manana', 'radio'),
            Option('pasado', 'radio'),
            Option('todos', 'radio')
        ),
        path='/home/pi/scripts/aemet.py',
        ispublic=True,
    )
    MENUS = RaspberryService(
        name='MENUS',
        command=Command(
            template='{PYTHON} {PATH} output -show {OPTIONS}',
            path='/home/pi/scripts/menus_resi.py',
        ),
        options=(
            Option('hora', 'time', include=False),
            Option('comida', 'radio'),
            Option('cena', 'radio'),
            Option('default', 'radio')
        ),
        path='/home/pi/scripts/menus_resi.py',
        ispublic=True,
    )

    VCS = RaspberryService(
        name='VCS',
        command=Command(
            # todo: crear command
            template='{PYTHON} {RUTA} {OPTIONS}',
            path='/home/pi/scripts/vcs.py',
        ),
        options=(
            Option('hora', 'time', include=False),
        ),
        path='/home/pi/scripts/vcs.py',
        data=('campus_username', 'campus_password'),
        ispublic=True
    )
    ENVIAR = RaspberryService(
        name='ENVIAR',
        command=Command(
            template='{PYTHON} {PATH} {OPTIONS}',
            path='/home/pi/scripts/enviar.py',
        ),
        options=(),
        path='/home/pi/scripts/enviar.py',
    )

    LOG = RaspberryService(
        name='LOG',
        command=Command(
            template=None,
            path=None,
            notify=False,
        ),
        options=(),
        extra_paths=(
            '/home/pi/scripts/backup.py', '/home/pi/scripts/ngrok.py', '/home/pi/scripts/ngrok2.py',
            '/home/pi/scripts/reboot.py', '/home/pi/scripts/serveo.py', '/home/pi/scripts/gestor_mail.py',
            '/home/pi/scripts/controller.py', '/home/pi/pull.sh'
        ),
        isabstract=True
    )

    UNKNOWN = RaspberryService(
        name='UNKOWN',
        command=Command(
            template=None,
            path=None,
            notify=False,
        ),
        options=(),
        isabstract=True
    )

    def __repr__(self):
        return self.__class__.__nombre__ + '.' + self.name

    def __str__(self):
        return self.name

    @staticmethod
    def get(basepath):

        if isinstance(basepath, RaspberryService):
            return basepath
        if isinstance(basepath, ServiceManager):
            return basepath.value

        basepath = os.path.basename(basepath).lower()
        for servicio in ServiceManager:
            if servicio.value.corresponds_with(basepath):
                return servicio.value

        warn(f"Unkown service: {basepath!r}", UnrecognisedServiceWarning)
        return ServiceManager.UNKNOWN.value

    @staticmethod
    def eval(algo):
        """Does the convertion str -> Servicios."""
        try:
            data = eval(algo, globals(), ServiceManager.__dict__)
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
                warn(f"Something may have gone wrong (data={data!r})", UnexpectedBehaviourWarning)

        return tuple(data)
