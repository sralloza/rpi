# -*- coding: utf-8 -*-

import json
import os
import sqlite3
from dataclasses import dataclass, field
from json import JSONDecodeError

from rpi.dns import RpiDns
from rpi.exceptions import UnrecognisedUsernameError, InvalidLauncherError
from rpi.launcher import IftttLauncher, NotifyRunLauncher, BaseLauncher
from rpi.rpi_logging import Logger
from .crontab_manager import CrontabManager
from .service_manager import ServiceManager, RaspberryService


@dataclass(init=False)
class User:
    """Represents a user."""
    username: str
    launcher: BaseLauncher
    isactive: bool
    email: str

    cronitems: list = field(init=False)
    isbanned: bool = field(init=False, repr=False)

    def __init__(self, username, launcher, isactive, email, *services):
        self.username = username
        self.launcher = launcher
        self.cronitems = None
        self.isactive = bool(isactive)
        self.isbanned = not self.isactive
        self.email = email

        if isinstance(services, str):
            self.services = (services,)
        else:
            if isinstance(services, tuple) and len(services) == 1:
                services = services[0]
                if isinstance(services, RaspberryService):
                    self.services = (services,)
                else:
                    self.services = services

        self.update_cronitems()

    def update_cronitems(self):
        """Updates all tasks created by user."""
        self.cronitems = CrontabManager.list_by_user(self)

    def new_task(self, command, user, hour, minutes):
        """Creates a new task."""
        CrontabManager.new(command, user, hour, minutes)
        self.update_cronitems()

    def __str__(self):
        return self.username


class UserManager(list):
    """Clase para gestionar los usuarios."""

    def __init__(self):
        super().__init__()
        self.path = None

    def __str__(self):
        return '\n'.join([repr(e) for e in self])

    @property
    def usernames(self):
        return tuple([x.username for x in self])

    @property
    def emails(self):
        return tuple([x.email for x in self])

    @classmethod
    def load(cls):
        """Carga todos los usuarios."""
        self = cls.__new__(cls)
        self.__init__()

        @dataclass
        class TempUser:
            username: str
            launcher: BaseLauncher
            isbanned: bool
            email: str
            services: tuple

        self.path = RpiDns.get('sqlite.django')

        if os.path.isfile(self.path) is False:
            logger = Logger.get(__file__, __name__)
            logger.critical('User database not found')
            raise FileNotFoundError('User database not found')

        self.con = sqlite3.connect(self.path)
        self.cur = self.con.cursor()
        self.cur.execute("select username, launcher, is_active, email, servicios from 'usuarios_usuario'")

        content = self.cur.fetchall()
        self.con.close()

        content = [TempUser(*x) for x in content]

        for user in content:
            username = user.username
            isbanned = user.isbanned
            email = user.email

            services = ServiceManager.eval(user.services)
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

            self.append(User(username, launcher, isbanned, email, services))

        return self

    def get_by_username(self, username):

        for user in self:
            if user.username == username:
                return user
        raise UnrecognisedUsernameError(f'Unknown username: {username!r}')


rpi_gu = UserManager.load()
