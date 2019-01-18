# -*- coding: utf-8 -*-

"""Services manager for raspberry pi scripts."""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple, Union
from warnings import warn

from rpi.exceptions import UnexpectedBehaviourWarning, MissingOptionsError, \
    InvalidOptionError


@dataclass
class Option:
    """Represents an option of a raspberry pi service."""

    name: str
    type: str
    include: bool = field(default=True)
    es: str = field(default=None)


@dataclass
class Command:
    """Represents a command that is executed by a RaspberryService."""
    template: Union[str, None]
    path: Union[str, None]
    notify: bool = field(default=True)
    preoption: str = field(default='')

    def __post_init__(self):
        if self.notify is True:
            if self.template.endswith(' ') is False:
                self.template += ' '
            self.template += '-notify {USERNAME}'

    def __format__(self, *args, **kwargs):
        assert isinstance(kwargs['OPTIONS'], (tuple, list))
        kwargs['OPTIONS'] = ' '.join([self.preoption + x for x in kwargs['OPTIONS']])
        return self.template.format(*args, **kwargs)

    def format(self, *args, **kwargs) -> str:
        """Returns the command ready to be executed."""
        return self.__format__(*args, **kwargs)


@dataclass(repr=False)
class RaspberryService:
    """Represents a service run by raspberry pi"""

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
    def options_names(self) -> tuple:
        """Returns all the option names, both english names and spanish names."""
        return tuple(self.option_names_en + self.option_names_es)

    @property
    def option_names_en(self) -> tuple:
        """Returns the option names in english."""
        return tuple(self.option_namespace.keys())

    @property
    def option_names_es(self) -> tuple:
        """Returns the option names in spanish"""
        return tuple([x for x in self.option_namespace.values() if x is not None])

    @property
    def option_namespace(self) -> dict:
        """Returns a dict of option language transformation: english_name -> spanish_name."""
        return {option.name: option.es for option in self.options}

    @property
    def filenames_with_ext(self):
        """list of filenames with extension (enviar.py, aemet.py, ...)."""
        return tuple([os.path.basename(x).lower() for x in self.all_paths])

    @property
    def filenames_without_ext(self) -> tuple:
        """list of filenames without extension (enviar, aemet, ...)."""
        return tuple(os.path.splitext(x)[0].lower() for x in self.filenames_with_ext)

    def corresponds_with(self, other: str) -> bool:
        """Checks if the string corresponds with this service. It checks the service name and
        the filepaths with and without extension.

        Args:
            other (str): anything that can identify a service.

        Returns:
            bool: indicating wether or not the identifier corresponds with this service.

        """

        other = os.path.basename(other).lower()

        if other == self.name.lower():
            return True

        if other in self.filenames_with_ext:
            return True

        if other in self.filenames_without_ext:
            return True

        return False

    def generate_command(self, **kwargs):
        """Returns the command ready to be executed."""

        kwargs.update(**RaspberryService.DEFAULT)
        kwargs.update(PATH=self.path)

        if 'options' in kwargs:
            kwargs['OPTIONS'] = kwargs['options']
            del kwargs['options']

        if 'username' in kwargs:
            kwargs['USERNAME'] = kwargs['username']
            del kwargs['username']

        try:
            for opt in kwargs['OPTIONS']:
                if opt not in self.options_names:
                    raise InvalidOptionError(
                        f'Option {opt!r} is not registered ({self.options_names!r})')
        except KeyError:
            raise MissingOptionsError('Options have not been specified')

        return self.command.format(**kwargs)


class ServicesManager(Enum):
    """Manager for the raspberry services."""

    AEMET = RaspberryService(
        name='AEMET',
        command=Command(
            template='{PYTHON} {PATH} {OPTIONS}',
            path='/home/pi/scripts/aemet.py',
            preoption='-',
        ),
        options=(
            Option('time', 'time', es='hora', include=False),
            Option('today', 'radio', es='hoy'),
            Option('tomorrow', 'radio', es='mañana'),
            Option('day-after', 'radio', es='pasado mañana'),
            Option('all', 'radio', es='todo')
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
            Option('time', 'time', es='hora', include=False),
            Option('launch', 'radio', es='comida'),
            Option('dinner', 'radio', es='cena'),
            Option('all', 'radio', es='todo')
        ),
        path='/home/pi/scripts/menus_resi.py',
        ispublic=True,
    )

    VCS = RaspberryService(
        name='VCS',
        command=Command(
            # todo: crear command
            template='{PYTHON} {PATH} {OPTIONS}',
            path='/home/pi/scripts/vcs.py',
        ),
        options=(
            Option('time', 'time', es='hora', include=False),
        ),
        path='/home/pi/scripts/vcs.py',
        data=('campus_username', 'campus_password'),
        ispublic=True
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
            '/home/pi/scripts/reboot.py', '/home/pi/scripts/serveo.py',
            '/home/pi/scripts/gestor_mail.py',
            '/home/pi/pull.sh',
        ),
        isabstract=True
    )

    TELEGRAM_BOT = RaspberryService(
        name='TELEGRAM_BOT',
        command=Command(
            template=None,
            path=None,
            notify=False
        ),
        options=(),
        path='/home/pi/scripts/telegram_bot.py',
        extra_paths=(),
        isabstract=True
    )

    CONTROLLER = RaspberryService(
        name='CONTROLLER',
        command=Command(
            template=None,
            path=None,
            notify=False
        ),
        options=(),
        path='/home/pi/scripts/controller.py',
        extra_paths=(),
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
    def get(basepath: str) -> RaspberryService:
        """Returns the service given its identifier."""

        logger = logging.getLogger(__name__)
        logger.debug('Trying to identify service from %r', basepath)

        if isinstance(basepath, RaspberryService):
            return basepath
        if isinstance(basepath, ServicesManager):
            return basepath.value

        basepath = os.path.basename(basepath).lower()
        for servicio in ServicesManager:
            if servicio.value.corresponds_with(basepath):
                return servicio.value

        logger.warning("Unkown service: %r", basepath)
        # warn(f"Unkown service: {basepath!r}", UnrecognisedServiceWarning)
        return ServicesManager.UNKNOWN.value

    # noinspection PyTypeChecker
    @staticmethod
    def eval(string_to_evaluate: str) -> Tuple[RaspberryService]:
        """Returns a list of services from a string representation of a list of services."""

        logger = logging.getLogger(__name__)
        logger.debug('Evaluating %r', string_to_evaluate)
        try:
            data = eval(string_to_evaluate, globals(), ServicesManager.__dict__)
        except SyntaxError:
            return tuple()

        try:
            data = list(data)
        except TypeError:
            data = [data, ]

        for i, _ in enumerate(data):
            try:
                data[i]: RaspberryService = data[i].value
            except AttributeError:
                warn(f"Something may have gone wrong (data={data!r})", UnexpectedBehaviourWarning)
                logger.warning("Something may have gone wrong (data=%r)", data)

        logger.debug('Evaluated: %r', data)

        return tuple(data)
