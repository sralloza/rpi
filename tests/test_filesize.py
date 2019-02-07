# def size(number_of_bytes, system=TRADITIONAL):
import os

import pytest

from rpi.filesize import size


def test_filesize():
    s1 = 0
    s2 = 10
    s3 = 10001
    s4 = 1000000
    s5 = 10 ** 9

    assert size(s1) == '0B'
    assert size(s2) == '10B'
    assert size(s3) == '9K'
    assert size(s4) == '976K'
    assert size(s5) == '953M'


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__), '-v'])
