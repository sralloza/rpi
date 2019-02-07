# -*- coding: utf-8 -*-

"""Manager of output files throw email."""

import datetime
import logging
import os

from rpi import ADMIN_EMAIL
from rpi import operating_system_in_brackets as osib
from rpi.connections import Connections
from rpi.custom_logging import LoggingInfo
from rpi.dns import RpiDns
from rpi.exceptions import NeccessaryArgumentError


def handle_request(resource_id: int)->tuple:
    """Gets the files and description according to resource id.

    Args:
        resource_id (int): id of the resource.

    Returns:
         tuple: files and description.

    """
    logger = logging.getLogger(__name__)
    if resource_id == 1:
        files, description = get_vcs_history()
    elif resource_id == 2:
        files, description = get_mail()
    elif resource_id == 3:
        files, description = get_menus_database()
    elif resource_id == 4:
        files, description = get_info_logs()
    else:
        logger.critical('%s is not a valid resource id', resource_id)
        raise TypeError(f'{resource_id} is not a valid resource id')

    return files, description


def print_info():
    """Prints the resources with its ids."""
    print('\n\n')
    print('--------BASES DE DATOS---------')
    print('1. Virtual Campus History')
    print('2. Raspberry Mail')
    print('3. Residence Menus')
    print('4. Today\'s log: ' + datetime.datetime.today().strftime('(%Y-%m-%d)'))
    print('-------------------------------')


def get_vcs_history():
    """Gets the info for the virtual campus scanner database."""
    description = 'Base de datos de links del Campus Virtual de la UVa'
    files = RpiDns.get('sqlite.vcs')
    return files, description


def get_mail():
    """Gets the info for the raspberry mail (users pi and www-data)."""
    description = 'Raspberry Mail'
    files = {RpiDns.get('textdb.mail-pi'): 'raspberry_mail.txt',
             RpiDns.get('textdb.mail-www-data'): 'raspberry_mail2.txt'}
    return files, description


def get_menus_database():
    """Gets the info for the menus database."""
    description = 'Menús Residencia Santiago'
    files = RpiDns.get('sqlite.menus_resi')
    return files, description


def get_info_logs():
    """Gets the info for all the logs files."""
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    description = 'Log ' + today

    files = {
        LoggingInfo.LOGS_APACHE_ACCESS: today + '.apache.access.log.txt',
        LoggingInfo.LOGS_APACHE_ERRROR: today + '.apache.error.log.txt'
    }

    for filename in os.listdir(LoggingInfo.LOGS_DAY_FOLDER):
        files[filename] = filename + '.txt'

    return files, description


def sender(resource_id=None, keys=False):
    """Main function."""
    logger = logging.getLogger(__name__)
    automatic = False

    if resource_id is not None:
        if resource_id in (1, 2, 3, 4):
            automatic = True
            logger.debug('Automatic sending request: %s', resource_id)

    if keys is True:
        print(' 1 |     2    |   3   |    4   ')
        print('CV | Rpi Mail | Menús | Log Hoy')
        return 0

    mail_message = '<h2><span style="color: #339966; font-family: cambria; font-size: 35px;">' \
                   'Petición aceptada: '

    if automatic is False:
        print_info()

        resource_id = int(input('Insert resource\'s id:  '))
        destiny = input('Destiny: ')
    else:
        destiny = ''

    destiny = destiny if destiny else ADMIN_EMAIL

    if automatic is False:
        logger.debug('Manual sending request: %s to %r', resource_id, destiny)

    about = 'Enviada '
    files, description = handle_request(resource_id)

    if files is None:
        logger.critical("'files' argument can't be None")
        raise NeccessaryArgumentError("'files' argument can't be None")

    about += description
    mail_message += about
    mail_message += '</span></h2><p>&nbsp;</p>'

    logger.debug('Sending file %r to %r', files, destiny)
    result_email = Connections.send_email(destiny, about, mail_message, files=files,
                                          origin='Rpi-Sender')
    if result_email is True:
        logger.debug('Shipping Manager %s: sent %s to %s', osib(), description, destiny)
    else:
        logger.debug('Shipping Manager %s: error sending %s to %s', osib(), description, destiny)

    return {'mail': result_email}
