import os

import pytest

from rpi import operating_system, operating_system_in_brackets


def test_operating_system():
    assert operating_system() in ('L', 'W')


def test_operating_system_in_brackets():
    assert operating_system_in_brackets() in ('(L)', '(W)')


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__), '-v'])
