import datetime
import logging
import os

from rpi import ADMIN_EMAIL
from rpi import operating_system_in_brackets as osib
from rpi.connections import Connections
from rpi.custom_logging import LoggingInfo
from rpi.dns import RpiDns
from rpi.exceptions import NeccessaryArgumentError


def sender_main(resource_id=None, keys=False):
    logger = logging.getLogger(__name__)
    automatic = False

    if resource_id is not None:
        if resource_id in (1, 2, 3, 4, 5):
            automatic = True
            logger.debug(f'Automatic sending request: {resource_id}')

    if keys is True:
        print(' 1 |     2    |   3   |    4   |    5   ')
        print('CV | Rpi Mail | Menús | Maildb | Log Hoy')
        return

    mail_message = '<h2><span style="color: #339966; font-family: cambria; font-size: 35px;">' \
                   'Petición aceptada: '

    if automatic is False:
        print('\n\n')
        print('--------BASES DE DATOS---------')
        print('1. Virtual Campus History')
        print('2. Raspberry Mail')
        print('3. Residence Menus')
        print('4. Raspberry Mail Data Base')
        print('5. Today\'s log: ' + datetime.datetime.today().strftime('(%Y-%m-%d)'))
        print('-------------------------------')

        resource_id = int(input('Insert resource\'s id:  '))
        destino = input('Destiny: ')
    else:
        destino = ''
    if destino == '':
        destino = ADMIN_EMAIL

    if automatic is False:
        logger.debug(f'Manual sending request: {resource_id} to {destino!r}')

    about = 'Enviada '
    if resource_id == 1:
        description = 'Base de datos de links del Campus Virtual de la UVa'
        file = RpiDns.get('sqlite.vcs')

    elif resource_id == 2:
        description = 'Raspberry Mail'
        file = {RpiDns.get('textdb.mail-pi'): 'raspberry_mail.txt',
                RpiDns.get('textdb.mail-www-data'): 'raspberry_mail2.txt'}

    elif resource_id == 3:
        description = 'Menús Residencia Santiago'
        file = RpiDns.get('sqlite.menus_resi')

    elif resource_id == 4:
        description = 'Raspberry Mail Database'
        file = RpiDns.get('sqlite.raspberry_mail')

    elif resource_id == 5:
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        description = 'Log ' + today
        path = RpiDns.get('folder.log')

        if path.endswith('/') is False:
            path += '/'

        file = {
            LoggingInfo.LOGS_APACHE_ACCESS: today + '.apache.access.log.txt',
            LoggingInfo.LOGS_APACHE_ERRROR: today + '.apache.error.log.txt'
        }

        for filename in os.listdir(LoggingInfo.LOGS_DAY_FOLDER):
            file[filename] = filename + '.txt'

    else:
        logger.critical(f'{resource_id} is not a valid resource id')
        raise TypeError(f'{resource_id} is not a valid resource id')

    if file is None:
        logger.critical("'file' argument can't be None")
        raise NeccessaryArgumentError("'file' argument can't be None")

    about += description
    mail_message += about
    mail_message += '</span></h2><p>&nbsp;</p>'

    logger.debug('Sending file %r to %r', file, destino)
    result_email = Connections.send_email(destino, about, mail_message, files=file,
                                          origin='Rpi-Sender')
    if result_email is True:
        logger.debug(f'Shipping Manager {osib()}: sent {description} to {destino}')
    else:
        logger.debug(f'Shipping Manager {osib()}: error sending {description} to {destino}')

    return {'mail': result_email}
