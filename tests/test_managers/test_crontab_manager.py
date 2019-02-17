import os

import pytest

from rpi.exceptions import ExistingJobError, CrontabError
from rpi.managers.crontab_manager import CrontabManager
from rpi.managers.services_manager import ServicesManager


class TestCrontabManager:
    def test_load(self):
        CrontabManager()

    def test_list_by_user_1(self):
        assert len(CrontabManager.list_by_user('test')) == 0

    def test_new(self):
        CrontabManager.new('/home/test/command', 'test', 22, 22)
        CrontabManager.new('/home/test/command2', 'test', 22, 22)
        CrontabManager.new('/home/test/python /home/test/script -option value', 'test', 22, 22)

        with pytest.raises(ExistingJobError, match='Job already exists'):
            CrontabManager.new('/home/test/command', 'test', 22, 22)

    def test_list_by_user_2(self):
        assert len(CrontabManager.list_by_user('test')) == 3

    def test_job_to_str(self):
        j1, j2, j3 = list(CrontabManager.list_by_user('test'))

        with pytest.raises(CrontabError, match='job couldn\'t be id as a service job'):
            CrontabManager.job_to_str(j1)

        with pytest.raises(CrontabError, match='job couldn\'t be id as a service job'):
            CrontabManager.job_to_str(j2)

        service, options = CrontabManager.job_to_str(j3)
        assert service == ServicesManager.UNKNOWN.value
        assert options == ''

    def test_delete_by_anything(self):
        j1, j2, j3 = [job for job in CrontabManager.list_by_user('test')]
        j1 = CrontabManager.job_to_hash(j1)
        j2 = str(CrontabManager.job_to_hash(j2))

        CrontabManager.delete_by_anything(j1)
        CrontabManager.delete_by_anything(j2)
        CrontabManager.delete_by_anything(j3)


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__), '-vs'])
