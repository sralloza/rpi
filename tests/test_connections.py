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

    with pytest.raises(NeccessaryArgumentError, match="The 'file' argument is needed in"):
        Connections.notify('test_title', 'test_message', 'test_user')

    with pytest.raises(NeccessaryArgumentError, match="Multicast can't be used without"):
        Connections.notify('test_title', 'test_message', 'multicast')

    with pytest.raises(PermissionError, match="'force' must be True in order to use broadcast."):
        Connections.notify('test_title', 'test_message', 'broadcast')

    random_user = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(15))

    with pytest.raises(UserNotFoundError, match=random_user):
        Connections.notify('test_title', 'test_message', random_user, force=True)

    assert Connections.notify('test_title', 'test_message', 'test', force=True) is True


def test_mail():
    with pytest.raises(InvalidMailAddressError, match="'test_destination' is not a valid email"):
        Connections.send_email('test_destination', 'test_subject', 'test_message')

    with pytest.raises(TypeError, match="destinations must be iterable or str"):
        Connections.send_email(18, 'test_subject', 'test_message')


def test_to_google_spreadsheets():
    data = tuple((random.randint(0, 10) for _ in range(10)))

    with pytest.raises(SpreadsheetNotFoundError, match='test_file'):
        Connections.to_google_spreadsheets('test_file', 'test_sheet', data)

    with pytest.raises(SheetNotFoundError, match='test_sheet'):
        Connections.to_google_spreadsheets('pylog', 'test_sheet', data)


def test_from_google_spreadsheets():
    with pytest.raises(SpreadsheetNotFoundError, match='test_file'):
        Connections.from_google_spreadsheets('test_file', 'test_sheet')

    with pytest.raises(SheetNotFoundError, match='test_sheet'):
        Connections.from_google_spreadsheets('pylog', 'test_sheet')

    data = Connections.from_google_spreadsheets('pylog', 'puertos')

    assert len(data) > 0


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__), '-v'])
