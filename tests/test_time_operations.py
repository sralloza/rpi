# def secs_to_str(seconds, abbreviated=False, integer=None, language='en'):
# def split_seconds(totalsegundos, days=False, entero=None):

import os

import pytest

from rpi.time_operations import split_seconds, secs_to_str


def test_split_seconds():
    s1 = 1
    s2 = 61
    s3 = 138
    s4 = 5642
    s5 = 56489
    s6 = 982645

    assert split_seconds(s1) == (0, 0, 1)
    assert split_seconds(s2) == (0, 1, 1)
    assert split_seconds(s3) == (0, 2, 18)
    assert split_seconds(s4) == (1, 34, 2)
    assert split_seconds(s5) == (15, 41, 29)
    assert split_seconds(s6) == (272, 57, 25)

    assert split_seconds(s1, days=True) == (0, 0, 0, 1)
    assert split_seconds(s2, days=True) == (0, 0, 1, 1)
    assert split_seconds(s3, days=True) == (0, 0, 2, 18)
    assert split_seconds(s4, days=True) == (0, 1, 34, 2)
    assert split_seconds(s5, days=True) == (0, 15, 41, 29)
    assert split_seconds(s6, days=True) == (11, 8, 57, 25)

    assert split_seconds(float(s1)) == (0, 0, 1)
    assert split_seconds(float(s2)) == (0, 1, 1)
    assert split_seconds(float(s3)) == (0, 2, 18)
    assert split_seconds(float(s4)) == (1, 34, 2)
    assert split_seconds(float(s5)) == (15, 41, 29)
    assert split_seconds(float(s6)) == (272, 57, 25)

    s1 = 0.2459
    s2 = 2.1266
    s3 = 5.1684
    s4 = 10.2166
    s5 = 65.1651

    assert split_seconds(s1, integer=False) == (0.0, 0.0, 0.25)
    assert split_seconds(s2, integer=False) == (0.0, 0.0, 2.13)
    assert split_seconds(s3, integer=False) == (0.0, 0.0, 5.17)
    assert split_seconds(s4, integer=False) == (0.0, 0.0, 10.22)
    assert split_seconds(s5, integer=False) == (0.0, 1.0, 5.17)


def test_secs_to_str():
    s1 = 1
    s2 = 61
    s3 = 138
    s4 = 5642
    s5 = 56489
    s6 = 982645

    assert secs_to_str(s1) == '1 second'
    assert secs_to_str(s2) == '1 minute and 1 second'
    assert secs_to_str(s3) == '2 minutes and 18 seconds'
    assert secs_to_str(s4) == '1 hour, 34 minutes and 2 seconds'
    assert secs_to_str(s5) == '15 hours, 41 minutes and 29 seconds'
    assert secs_to_str(s6) == '11 days, 8 hours, 57 minutes and 25 seconds'

    assert secs_to_str(s1, abbreviated=True) == '1 s'
    assert secs_to_str(s2, abbreviated=True) == '1 m and 1 s'
    assert secs_to_str(s3, abbreviated=True) == '2 m and 18 s'
    assert secs_to_str(s4, abbreviated=True) == '1 h, 34 m and 2 s'
    assert secs_to_str(s5, abbreviated=True) == '15 h, 41 m and 29 s'
    assert secs_to_str(s6, abbreviated=True) == '11 d, 8 h, 57 m and 25 s'

    assert secs_to_str(s1, language='es') == '1 segundo'
    assert secs_to_str(s2, language='es') == '1 minuto y 1 segundo'
    assert secs_to_str(s3, language='es') == '2 minutos y 18 segundos'
    assert secs_to_str(s4, language='es') == '1 hora, 34 minutos y 2 segundos'
    assert secs_to_str(s5, language='es') == '15 horas, 41 minutos y 29 segundos'
    assert secs_to_str(s6, language='es') == '11 días, 8 horas, 57 minutos y 25 segundos'

    assert secs_to_str(s1, abbreviated=True, language='es') == '1 s'
    assert secs_to_str(s2, abbreviated=True, language='es') == '1 m y 1 s'
    assert secs_to_str(s3, abbreviated=True, language='es') == '2 m y 18 s'
    assert secs_to_str(s4, abbreviated=True, language='es') == '1 h, 34 m y 2 s'
    assert secs_to_str(s5, abbreviated=True, language='es') == '15 h, 41 m y 29 s'
    assert secs_to_str(s6, abbreviated=True, language='es') == '11 d, 8 h, 57 m y 25 s'


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__), '-vs'])
