# -*- coding: utf-8 -*-

import json
import logging
import os
import sqlite3
from dataclasses import dataclass, field
from json import JSONDecodeError

from rpi.dns import RpiDns
from rpi.exceptions import UserNotFoundError
from rpi.launcher import IftttLauncher, NotifyRunLauncher, BaseLauncher, TelegramLauncher, \
    InvalidLauncher
from .crontab_manager import CrontabManager
from .services_manager import ServicesManager, RaspberryService

# TODO - STOP USING DATACLASSES

@dataclass(init=False)
class User:
    """Represents a user."""
    username: str
    launcher: BaseLauncher
    is_active: bool
    email: str
    is_superuser: bool
    is_staff: bool

    cronitems: list = field(init=False, hash=False, repr=False)
    is_banned: bool = field(init=False, repr=False)

    def __init__(self, username, launcher, is_active, is_superuser, is_staff, email, *services):
        self.username = username
        self.launcher = launcher
        self.cronitems = None
        self.is_active = bool(is_active)
        self.is_banned = not self.is_active
        self.email = email
        self.is_superuser = bool(is_superuser)
        self.is_staff = bool(is_staff)

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

    def __hash__(self):
        o = (
            self.username, self.is_active, self.is_banned,
            self.email, self.is_superuser, self.is_staff
        )
        return hash(o)

    def __eq__(self, other):
        return hash(self) == hash(other)

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
        self.logger = logging.getLogger(__name__)
        self.path = None
        self.con = None
        self.cur = None

        self.load()

    def __contains__(self, item):
        return item in self.usernames

    def __str__(self):
        return '\n'.join([repr(e) for e in self])

    @property
    def usernames(self):
        result = tuple([x.username for x in self])
        return result

    @property
    def emails(self):
        result = tuple([x.email for x in self])
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
            is_active: bool
            email: str
            services: tuple
            is_superuser: bool
            is_staff: bool

        self.path = RpiDns.get('sqlite.django')

        if os.path.isfile(self.path) is False:
            self.logger.critical('User database not found (%r)', self.path)
            raise FileNotFoundError(f'User database not found ({self.path})')

        self.con = sqlite3.connect(self.path)
        self.cur = self.con.cursor()
        self.cur.execute(
            "select username, launcher, is_active, email, servicios, "
            "is_superuser, is_staff from 'usuarios_usuario'")

        content = self.cur.fetchall()
        self.con.close()

        content = [TempUser(*x) for x in content]

        for user in content:
            username = user.username
            is_active = user.is_active
            email = user.email
            is_superuser = user.is_superuser
            is_staff = user.is_staff

            # noinspection PyTypeChecker
            services = ServicesManager.eval(user.services)
            try:
                launcher = json.loads(user.launcher)
            except JSONDecodeError:
                launcher = {"type": 'Invalid'}

            if launcher["type"] == 'IFTTT':
                launcher = IftttLauncher(launcher["config"])
            elif launcher["type"] == "NotifyRun":
                launcher = NotifyRunLauncher(launcher["config"])
            elif launcher['type'] == "Telegram":
                launcher = TelegramLauncher(launcher['config'])
            else:
                launcher = InvalidLauncher()

            self.append(
                User(username, launcher, is_active, is_superuser, is_staff, email, services))

        self.logger.debug('Users loaded')
        return self

    @staticmethod
    def get_by_username(username) -> User:
        self = UsersManager.__new__(UsersManager)
        self.__init__()

        for user in self:
            if user.username == username:
                return user
        self.logger.critical(f'Unknown username: {username!r}')
        raise UserNotFoundError(f'Unknown username: {username!r}')

    @staticmethod
    def get_by_telegram_id(chat_id) -> User:
        self = UsersManager.__new__(UsersManager)
        self.__init__()

        chat_id = int(chat_id)
        for user in self:
            if isinstance(user.launcher, TelegramLauncher):
                if user.launcher.chat_id == chat_id:
                    return user
        self.logger.critical(f'Unknown chat_id: {chat_id!r}')
        raise UserNotFoundError(f'Unknown chat_id: {chat_id!r}')
