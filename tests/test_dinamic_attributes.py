# class DinamicAttributes:
#     def __setitem__(self, name, value): pass
#     def __delitem__(self, name): pass
#     def __contains__(self, name): pass
#     def dict(self): pass
#     def __repr__(self): pass
import os

import pytest

from rpi.dinamic_attributes import DinamicAttributes


@pytest.fixture(scope='module')
def d1():
    aux_dict = {'Peter': 'pan', 'GNU': 'linux', 'foo': 'bar'}
    return DinamicAttributes(dict=aux_dict)


@pytest.fixture(scope='module')
def d2():
    return DinamicAttributes(Peter='pan', GNU='linux', foo='bar')


@pytest.fixture(scope='module')
def d3():
    d3 = DinamicAttributes()
    d3.Peter = 'pan'
    d3.GNU = 'linux'
    d3.foo = 'bar'
    return d3


@pytest.fixture(scope='module')
def d4():
    d4 = DinamicAttributes()
    d4['Peter'] = 'pan'
    d4['GNU'] = 'linux'
    d4['foo'] = 'bar'
    return d4


def test_dinamic_attributes(d1, d2, d3, d4):
    assert d1.Peter == d2.Peter == d3.Peter == d4.Peter
    assert d1.GNU == d2.GNU == d3.GNU == d4.GNU
    assert d1.foo == d2.foo == d3.foo == d4.foo

    assert d1.Peter == 'pan'
    assert d2.GNU == 'linux'
    assert d3.foo == 'bar'

    d1.Peter = d2.Peter = d3.Peter = d4.Peter = 'fraud'

    assert d1.Peter == d2.Peter == d3.Peter == d4.Peter == 'fraud'

    assert d1.dict == d2.dict == d3.dict == d4.dict

    repr1 = repr(d1).replace('1', '0')
    repr2 = repr(d2).replace('1', '0')
    repr3 = repr(d3).replace('1', '0')
    repr4 = repr(d4).replace('1', '0')

    assert repr1 == repr2 == repr3 == repr4


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__), '-v'])
