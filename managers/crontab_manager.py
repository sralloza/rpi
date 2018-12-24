# -*- coding: utf-8 -*-

from crontab import CronTab, CronItem

from rpi import operating_system
from rpi.exceptions import JobNotFoundError, ExistingJobError, InvalidArgumentError


class CrontabManager(object):
    """Crontab interface"""
    BASE = '/usr/local/bin/python3 '

    def __init__(self):
        if operating_system() == 'W':
            self.cron = CronTab(tabfile='D:/PYTHON/raspberry_pi/rpi/crontab.txt')
        else:
            self.cron = CronTab(user=True)

    def __iter__(self):
        return iter(self.cron)

    @staticmethod
    def new(command, user, hour, minutes):
        self = CrontabManager.__new__(CrontabManager)
        self.__init__()

        username = CrontabManager.user_to_username(user)

        new_job = self.cron.new(command, comment=username)
        new_job.hour.on(hour)
        new_job.minutes.on(minutes)

        counter = 0

        for job in self.cron.find_comment(username):
            if CrontabManager.job_to_hash(job) == CrontabManager.job_to_hash(new_job):
                counter += 1

        if counter > 1:
            raise ExistingJobError(f'Job already exists: {new_job!r}')
        self.cron.write()

    @staticmethod
    def delete(anything):
        # TODO: UNDERSTAND WHAT THE FUCK DOES THIS DO
        self = CrontabManager.__new__(CrontabManager)
        self.__init__()

        if isinstance(anything, CronItem):
            hashcode = CrontabManager.job_to_hash(anything)
        elif isinstance(anything, int):
            hashcode = anything
        elif isinstance(anything, str):
            hashcode = int(anything)
        else:
            raise InvalidArgumentError(f'Tipo incorrecto ({type(anything).__name__!r})')
        return self.delete_by_hash(hashcode)

    @staticmethod
    def delete_by_hash(hashcode):
        self = CrontabManager.__new__(CrontabManager)
        self.__init__()

        select = None
        jobs = list(self.cron)

        for job in jobs:
            if self.job_to_hash(job) == hashcode:
                select = job
                self.cron.remove(job)

        if select is None:
            raise JobNotFoundError(f'Can not find job with hash={hashcode!r}')

        self.cron.write()

    @staticmethod
    def list_by_user(user):
        self = CrontabManager.__new__(CrontabManager)
        self.__init__()

        username = CrontabManager.user_to_username(user)

        return list(self.cron.find_comment(username))

    @staticmethod
    def job_to_hash(job: CronItem):
        return hash(str(vars(job)))

    @staticmethod
    def user_to_username(user):
        try:
            username = user.username
        except AttributeError:
            username = user
        return username
