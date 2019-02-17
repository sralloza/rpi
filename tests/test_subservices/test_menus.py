import datetime
import os

import pytest

from rpi.subservices.menus import extend_date, get_date, MenusDatabaseManager


def test_extend_date():
    d0 = '01/01/2001'
    d1 = '15/08/1998'
    d2 = '07/11/1958'
    d3 = '13/12/1961'
    d4 = '11/05/2004'
    d5 = '50/12/2018'
    d6 = '05/19/2018'
    d7 = '13/03/2016'
    d8 = '29/02/2018'
    d9 = '29/02/2020'

    assert extend_date(d0) == 'DÍA: 01 DE ENERO DE 2001 (LUNES)'
    assert extend_date(d1) == 'DÍA: 15 DE AGOSTO DE 1998 (SÁBADO)'
    assert extend_date(d2) == 'DÍA: 07 DE NOVIEMBRE DE 1958 (VIERNES)'
    assert extend_date(d3) == 'DÍA: 13 DE DICIEMBRE DE 1961 (MIÉRCOLES)'
    assert extend_date(d4) == 'DÍA: 11 DE MAYO DE 2004 (MARTES)'
    assert extend_date(d5) == '50/12/2018'
    assert extend_date(d6) == '05/19/2018'
    assert extend_date(d7) == 'DÍA: 13 DE MARZO DE 2016 (DOMINGO)'
    assert extend_date(d8) == '29/02/2018'
    assert extend_date(d9) == 'DÍA: 29 DE FEBRERO DE 2020 (SÁBADO)'


def test_get_date():
    today = datetime.datetime.today().date()
    assert get_date() == (today.day, today.month, today.year)


class TestMenusDatabaseManager:
    def test_get_update(self):
        update = MenusDatabaseManager().get_update()
        assert isinstance(update, datetime.datetime)

    def test_extract_links(self):
        links = MenusDatabaseManager().extract_links()
        assert len(links) > 0
        assert isinstance(links, tuple)

    def test_extract_menu_data(self):
        menus_data = MenusDatabaseManager().extract_menus_data()
        assert len(menus_data) > 0
        assert isinstance(menus_data, tuple)

    def test_contains(self):
        with pytest.raises(TypeError, match='Only links are accepted'):
            _ = 4 in MenusDatabaseManager()


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__), '-vs'])
