# -*- coding: utf-8 -*-

import json
import os
import sqlite3
from dataclasses import dataclass, field
from json import JSONDecodeError

from rpi.dns import RpiDns
from rpi.exceptions import UnrecognisedUsernameError, InvalidLauncherError
from rpi.launcher import IftttLauncher, NotifyRunLauncher, BaseLauncher, TelegramLauncher
from rpi.rpi_logging import Logging
from .crontab_manager import CrontabManager
from .services_manager import ServicesManager, RaspberryService


@dataclass(init=False, unsafe_hash=True)
class User:
    """Represents a user."""
    username: str
    launcher: BaseLauncher
    isactive: bool
    email: str

    cronitems: list = field(init=False, hash=False)
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


class UsersManager(list):
    """Clase para gestionar los usuarios."""

    def __init__(self):
        super().__init__()
        self.logger = Logging.get(__file__, __name__)
        self.path = None
        self.con = None
        self.cur = None

        self.load()

    def __str__(self):
        return '\n'.join([repr(e) for e in self])

    @property
    def usernames(self):
        result = tuple([x.username for x in self])
        self.logger.debug(f'Returning list of usernames - {result!r}')
        return result

    @property
    def emails(self):
        result = tuple([x.email for x in self])
        self.logger.debug(f'Returning list of emails - {result!r}')
        return result

    def save_launcher(self, username):
        for user in self:
            if user.username == username:
                self.con = sqlite3.connect(self.path)
                self.cur = self.con.cursor()

                data = (json.dumps(user.launcher.to_json()), user.username)
                self.cur.execute('update usuarios_usuario set launcher=? where username=?', data)
                self.con.commit()
                self.con.close()
                self.logger.debug(f'Saved launcher for {username!r}')
                return True
        self.logger.debug(f'Could not save launcher for {username!r}')
        return False

    def load(self):
        """Carga todos los usuarios."""
        self.logger.debug('Loading users')

        @dataclass
        class TempUser:
            username: str
            launcher: BaseLauncher
            isactive: bool
            email: str
            services: tuple

        self.path = RpiDns.get('sqlite.django')

        if os.path.isfile(self.path) is False:
            self.logger.critical('User database not found')
            raise FileNotFoundError('User database not found')

        self.con = sqlite3.connect(self.path)
        self.cur = self.con.cursor()
        self.cur.execute("select username, launcher, is_active, email, servicios from 'usuarios_usuario'")

        content = self.cur.fetchall()
        self.con.close()

        content = [TempUser(*x) for x in content]

        for user in content:
            username = user.username
            isbanned = user.isactive
            email = user.email

            services = ServicesManager.eval(user.services)
            try:
                launcher = json.loads(user.launcher)
            except JSONDecodeError:
                continue

            if launcher["type"] == 'IFTTT':
                launcher = IftttLauncher(launcher["url"])
            elif launcher["type"] == "NotifyRun":
                launcher = NotifyRunLauncher(launcher["url"])
            elif launcher['type'] == "Telegram":
                launcher = TelegramLauncher(launcher['chat_id'])
            else:
                raise InvalidLauncherError()

            self.append(User(username, launcher, isbanned, email, services))

        self.logger.debug('Users loaded')
        return self

    def get_by_username(self, username):
        self.logger.debug('Getting user by username - {username!r}')
        for user in self:
            if user.username == username:
                return user
        self.logger.critical(f'Unknown username: {username!r}')
        raise UnrecognisedUsernameError(f'Unknown username: {username!r}')
