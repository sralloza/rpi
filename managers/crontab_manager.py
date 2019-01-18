# -*- coding: utf-8 -*-

"""Manager for linux crontab."""

import logging
import os
import re
from typing import Union, List

from crontab import CronTab, CronItem

from rpi import operating_system
from rpi.exceptions import JobNotFoundError, ExistingJobError, InvalidArgumentError
from rpi.managers.services_manager import ServicesManager
from rpi.managers.users_manager import User


class CrontabManager:
    """Crontab interface"""
    BASE = '/usr/local/bin/python3 '

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        if operating_system() == 'W':
            self.cron = CronTab(tabfile='D:/PYTHON/raspberry_pi/rpi/crontab.txt')
        else:
            self.cron = CronTab(user=True)

    def __iter__(self):
        return iter(self.cron)

    @staticmethod
    def new(command: str, user: Union[User, str], hour: int, minutes: int):
        """Creates a new task for crontab.

        Args:
            command (str): command to execute.
            user (Union[User, str]): user who wants to execute the command.
            hour (int): hour of the time when the command will be executed.
            minutes (int): minutes of the time when the command will be executed.

        """
        self = CrontabManager.__new__(CrontabManager)
        self.__init__()

        self.logger.debug('Trying to add a CronItem (%r, %r, %r, %r)', command, user, hour, minutes)
        username = CrontabManager.user_to_username(user)

        new_job = self.cron.new(command, comment=username)
        new_job.hour.on(hour)
        new_job.minutes.on(minutes)

        counter = 0

        for job in self.cron.find_comment(username):
            if CrontabManager.job_to_hash(job) == CrontabManager.job_to_hash(new_job):
                counter += 1

        if counter > 1:
            self.logger.critical('Job already exists: %r', new_job)
            raise ExistingJobError(f'Job already exists: {new_job!r}')

        self.cron.write()
        self.logger.debug('Job created and saved successfully')

    @staticmethod
    def delete_by_anything(anything: Union[CronItem, int, str]):
        """Deletes a job, regardless the type of anything (almost).

        Args:
            anything (Union[CronItem, int, str]): Can be a CronItem, or a hascode.

        Raises:
            InvalidArgumentError: if anything is not a CronItem, int or str.
            JobNotFoundError: if there is no job with that hashcode.

        """
        self = CrontabManager.__new__(CrontabManager)
        self.__init__()

        self.logger.debug('Trying to delete by anything - %r', anything)

        if isinstance(anything, CronItem):
            hashcode = CrontabManager.job_to_hash(anything)
        elif isinstance(anything, int):
            hashcode = anything
        elif isinstance(anything, str):
            hashcode = int(anything)
        else:
            self.logger.critical('Incorrect type (%r)', type(anything).__name__)
            raise InvalidArgumentError(f'Incorrect type ({type(anything).__name__!r})')

        return self.delete_by_hash(hashcode)

    @staticmethod
    def delete_by_hash(hashcode: int):
        """Deletes a job given its hash.

        Args:
            hashcode (int): hashcode of the job to delete.

        Raises:
            JobNotFoundError: if there is no job with that hashcode.

        """
        self = CrontabManager.__new__(CrontabManager)
        self.__init__()

        self.logger.debug('Trying to delete job by hash - %s', hashcode)

        select = None
        jobs = list(self.cron)

        for job in jobs:
            if self.job_to_hash(job) == hashcode:
                select = job
                self.cron.remove(job)

        if select is None:
            self.logger.critical('Can not find job with hash=%r', hashcode)
            raise JobNotFoundError(f'Can not find job with hash={hashcode!r}')

        self.cron.write()
        self.logger.debug('Job successfully deleted - %r', select)

    @staticmethod
    def list_by_user(user) -> tuple:
        """Returns a list of the cronitems that belong to a certain user.

        Args:
            user (Union[User, str]): user to get the list of cronitems from.

        Returns:
            tuple: list of cronitems of the user.

        """
        self = CrontabManager.__new__(CrontabManager)
        self.__init__()

        username = CrontabManager.user_to_username(user)
        result = tuple(self.cron.find_comment(username))

        logger = logging.getLogger(__name__)
        logger.debug('Returning list of cronitems by user %r', username)

        return result

    @staticmethod
    def job_to_hash(job: CronItem) -> int:
        """Returns a hash from a job.

        Args:
            job (CronItem): job to get the hash from.

        Returns:
            int: hash of the cronitem.

        """
        logger = logging.getLogger(__name__)
        result = hash(str(vars(job)))

        logger.debug('Returning hash %r from job %r', result, job)
        return result

    @staticmethod
    def user_to_username(user: Union[User, str]) -> str:
        """Returns the username from a user.

        Args:
            user (Union[User, str]): user to get the username from.

        Returns:
            str: username from the user.

        """
        try:
            username = user.username
        except AttributeError:
            username = user
        logger = logging.getLogger(__name__)
        logger.debug('Returning username %r from user %s', username, user)
        return username

    @staticmethod
    def job_to_str(job: CronItem, admin: bool = False) -> tuple:
        """Parses a job into and returns the service, options and username of it.

        Args:
            job (CronItem): Job to parse.
            admin (bool): if is True, it will return the username too. If not, it will only return
                the service and options.

        Returns:
            tuple: information compress in a tuple.

        """
        command_pattern = re.compile(
            r'(?P<PYTHON>[\w/.]+)\s(?P<SERVICE_PATH>[\w/.]+)\s(?P<EXTRA_ARGS>[\w\-\s]+)')

        service = ServicesManager.get(
            command_pattern.search(job.command).groupdict()['SERVICE_PATH'])

        options: Union[List[str], str] = os.path.basename(job.command).split(' ')[1:]

        try:
            options.remove(job.comment)
            options.remove('-notify')
        except ValueError:
            pass

        for i, _ in enumerate(options):
            options[i] = options[i].lstrip(service.command.preoption)

        i = 0
        while i < len(options):
            if options[i] not in service.options_names:
                options.remove(options[i])
                i = 0
            else:
                if options[i] in service.option_names_en:
                    options[i] = service.option_namespace[options[i]]
                i += 1

        options = ' '.join(options)

        if admin is False:
            return service, options

        return service, options, job.comment
