# -*- coding: utf-8 -*-

import argparse
import datetime
import time

from rpi import operating_system_in_brackets as osib, ADMIN_EMAIL
from rpi.connections import Connections
from rpi.dns import RpiDns
from rpi.exceptions import NeccessaryArgumentError
from rpi.rpi_logging import Logger

logger = Logger.get(__file__, __name__)


def shipping_main(resource_id=None, keys=False):
    automatic = False
    realfilename = None

    if resource_id is not None:
        if resource_id in (1, 2, 3, 4, 5, 6):
            resource_id = resource_id
            automatic = True
            logger.debug(f'Automatic sending request: {resource_id}')

    if keys is True:
        print(' 1 |  2   |    3     |   4   |    5   |    6   ')
        print('CV | Logs | Rpi Mail | Menús | Maildb | Log Hoy')
        return

    mail_message = '<h2><span style="color: #339966; font-family: cambria; font-size: 35px;">Petición aceptada: '

    if automatic is False:
        print('\n\n')
        print('--------BASES DE DATOS---------')
        print('1. Virtual Campus History')
        print('2. Logs')
        print('3. Raspberry Mail')
        print('4. Residence Menus')
        print('5. Raspberry Mail Data Base')
        print('6. Today\'s log: ' + datetime.datetime.today().strftime('(%Y-%m-%d)'))
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
        description = 'Logs'
        file = RpiDns.get('sqlite.log')

    elif resource_id == 3:
        description = 'Raspberry Mail'
        file = [RpiDns.get('textdb.mail-pi'), RpiDns.get('textdb.mail-www-data')]
        realfilename = 'raspberry_mail.txt'

    elif resource_id == 4:
        description = 'Menús Residencia Santiago'
        file = RpiDns.get('sqlite.menus_resi')

    elif resource_id == 5:
        description = 'Raspberry Mail Database'
        file = RpiDns.get('sqlite.raspberry_mail')

    elif resource_id == 6:
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        description = 'Log ' + today
        path = RpiDns.get('folder.log')

        if path.endswith('/') is False:
            path += '/'

        file = path + today + '.log'
        realfilename = today + '.log.txt'

    else:
        logger.critical(f'{resource_id} is not a valid resource id')
        raise TypeError(f'{resource_id} is not a valid resource id')

    if file is None:
        logger.critical("'file' argument can't be None")
        raise NeccessaryArgumentError("'file' argument can't be None")

    about += description
    mail_message += about
    mail_message += '</span></h2><p>&nbsp;</p>'

    result_email = Connections.send_email(destino, about, mail_message, files={file: realfilename}, origin='Rpi-Sender')
    if result_email is True:
        result_notif = Connections.notify('Shipping manager', 'Request accepted:\n' + about, file=__file__)
        logger.debug(f'Shipping Manager {osib()}: sent {description} to {destino}')
    else:
        result_notif = Connections.notify('Shipping manager', 'Error sending' + description, file=__file__)
        logger.debug(f'Shipping Manager {osib()}: error sending {description} to {destino}')

    return {'mail': result_email, 'notification': result_notif}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('id', help='Resource id')
    parser.add_argument('-keys', action='store_true',
                        help='Show correspondences resource - id')

    opt = vars(parser.parse_args())

    t0 = time.time()
    shipping_main(resource_id=opt['id'], keys=opt['keys'])
    logger.debug(f'Execution time of enviar: {time.time() - t0:.2f} s')
