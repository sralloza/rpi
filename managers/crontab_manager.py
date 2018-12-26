# -*- coding: utf-8 -*-

from crontab import CronTab, CronItem

from rpi import operating_system
from rpi.exceptions import JobNotFoundError, ExistingJobError, InvalidArgumentError
from rpi.rpi_logging import Logging


class CrontabManager(object):
    """Crontab interface"""
    BASE = '/usr/local/bin/python3 '

    def __init__(self):
        self.logger = Logging.get(__file__, __name__)
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

        self.logger.debug(f'Trying to add a CronItem ({command!r}, {user!r}, {hour!r}, {minutes!r})')
        username = CrontabManager.user_to_username(user)

        new_job = self.cron.new(command, comment=username)
        new_job.hour.on(hour)
        new_job.minutes.on(minutes)

        counter = 0

        for job in self.cron.find_comment(username):
            if CrontabManager.job_to_hash(job) == CrontabManager.job_to_hash(new_job):
                counter += 1

        if counter > 1:
            self.logger.critical(f'Job already exists: {new_job!r}')
            raise ExistingJobError(f'Job already exists: {new_job!r}')

        self.cron.write()
        self.logger.debug('Job created and saved successfully')

    @staticmethod
    def delete_by_anything(anything):
        # TODO: UNDERSTAND WHAT THE FUCK DOES THIS DO
        self = CrontabManager.__new__(CrontabManager)
        self.__init__()

        self.logger.debug(f'Trying to delete by anything - {anything!r}')

        if isinstance(anything, CronItem):
            hashcode = CrontabManager.job_to_hash(anything)
        elif isinstance(anything, int):
            hashcode = anything
        elif isinstance(anything, str):
            hashcode = int(anything)
        else:
            self.logger.critical(f'Tipo incorrecto ({type(anything).__name__!r})')
            raise InvalidArgumentError(f'Tipo incorrecto ({type(anything).__name__!r})')

        return self.delete_by_hash(hashcode)

    @staticmethod
    def delete_by_hash(hashcode):
        self = CrontabManager.__new__(CrontabManager)
        self.__init__()

        self.logger.debug(f'Trying to delete job by hash - {hashcode}')

        select = None
        jobs = list(self.cron)

        for job in jobs:
            if self.job_to_hash(job) == hashcode:
                select = job
                self.cron.remove(job)

        if select is None:
            self.logger.critical(f'Can not find job with hash={hashcode!r}')
            raise JobNotFoundError(f'Can not find job with hash={hashcode!r}')

        self.cron.write()
        self.logger.debug(f'Job successfully deleted - {select!r}')

    @staticmethod
    def list_by_user(user):
        self = CrontabManager.__new__(CrontabManager)
        self.__init__()

        username = CrontabManager.user_to_username(user)
        result = list(self.cron.find_comment(username))

        logger = Logging.get(__file__, __name__)
        logger.debug(f'Returning list of cronitems by user {username!r}')

        return result

    @staticmethod
    def job_to_hash(job: CronItem):
        logger = Logging.get(__file__, __name__)
        result = hash(str(vars(job)))

        logger.debug(f'Returning hash {result!r} from job {job!r}')
        return result

    @staticmethod
    def user_to_username(user):
        try:
            username = user.username
        except AttributeError:
            username = user
        logger = Logging.get(__file__, __name__)
        logger.debug(f'Returning username {username!r} from user {user!r}')
        return username
