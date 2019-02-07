import os
import random
import string

import pytest

from rpi import operating_system
from rpi.connections import Connections
from rpi.exceptions import NeccessaryArgumentError, UserNotFoundError, InvalidMailAddressError, \
    SpreadsheetNotFoundError, SheetNotFoundError


def test_connections_disable():
    status = operating_system() == 'W'
    assert Connections.DISABLE == status


def test_notification():
    Connections.DISABLE = False

    with pytest.raises(NeccessaryArgumentError) as ex:
        Connections.notify('test_title', 'test_message', 'test_user')

    assert str(ex.value) == "The 'file' argument is needed in order to check permissions."

    with pytest.raises(NeccessaryArgumentError) as ex:
        Connections.notify('test_title', 'test_message', 'multicast')
    assert str(ex.value) == "Multicast can't be used without the 'file' argument."

    with pytest.raises(PermissionError) as ex:
        Connections.notify('test_title', 'test_message', 'broadcast')
    assert str(ex.value) == "'force' must be True in order to use broadcast."

    random_user = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(15))

    with pytest.raises(UserNotFoundError) as ex:
        Connections.notify('test_title', 'test_message', random_user, force=True)
    assert random_user in str(ex.value)

    assert Connections.notify('test_title', 'test_message', 'test', force=True) is False


def test_mail():
    with pytest.raises(InvalidMailAddressError) as ex:
        Connections.send_email('test_destination', 'test_subject', 'test_message')
    assert str(ex.value) == "'test_destination' is not a valid email address."

    with pytest.raises(TypeError) as ex:
        Connections.send_email(18, 'test_subject', 'test_message')
    assert 'destinations must be iterable or str' in str(ex.value)


def test_to_google_spreadsheets():
    data = tuple((random.randint(0, 10) for _ in range(10)))

    with pytest.raises(SpreadsheetNotFoundError) as ex:
        Connections.to_google_spreadsheets('test_file', 'test_sheet', data)
    assert 'test_file' in str(ex.value)

    with pytest.raises(SheetNotFoundError) as ex:
        Connections.to_google_spreadsheets('pylog', 'test_sheet', data)
    assert 'test_sheet' in str(ex.value)


def test_from_google_spreadsheets():
    with pytest.raises(SpreadsheetNotFoundError) as ex:
        Connections.from_google_spreadsheets('test_file', 'test_sheet')
    assert 'test_file' in str(ex.value)

    with pytest.raises(SheetNotFoundError) as ex:
        Connections.from_google_spreadsheets('pylog', 'test_sheet')
    assert 'test_sheet' in str(ex.value)

    data = Connections.from_google_spreadsheets('pylog', 'puertos')

    assert len(data) > 0


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__), '-v'])
