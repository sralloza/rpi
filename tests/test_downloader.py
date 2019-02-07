# class Downloader(requests.Session):
#     def __init__(self, retries=10, silenced=False):
#     def get(self, url, **kwargs):
#     def post(self, url, data=None, json=None, **kwargs):
import os

import pytest

from rpi.downloader import Downloader

TEST_SERVER = 'http://httpbin.org/'


@pytest.fixture(scope='module')
def downloader(*args, **kwargs):
    return Downloader(*args, **kwargs)


def test_get(downloader):
    assert downloader.get(TEST_SERVER + 'get').status_code == 200


def test_post(downloader):
    assert downloader.post(TEST_SERVER + 'post', data={'peter': 'pan'}).status_code == 200


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__), '-v'])
