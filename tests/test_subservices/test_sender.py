# def get_mail():
# def get_menus_database():
# def get_info_logs():
# def sender(resource_id=None, keys=False):
import platform

import pytest

from rpi.subservices.sender import handle_request, get_vcs_history, get_mail, get_menus_database, \
    get_info_logs


def test_handle_request():
    with pytest.raises(TypeError, match='is not a valid resource id'):
        handle_request(2020)

    with pytest.raises(TypeError, match='is not a valid resource id'):
        handle_request(-95)

    files, description = handle_request(1)
    assert files
    assert description


def test_get_vcs_history():
    files, description = get_vcs_history()
    assert 'Base de datos de links del Campus Virtual de la UVa' in description
    assert platform.system().lower() in files


def test_get_mail():
    files, description = get_mail()
    assert 'Raspberry Mail' in description
    assert len(files) > 0


def test_get_menus_database():
    files, description = get_menus_database()
    assert 'Menús Residencia Santiago' in description
    assert platform.system().lower() in files


def test_get_info_logs():
    files, description = get_info_logs()
    assert 'Log' in description
    assert len(files) > 0
