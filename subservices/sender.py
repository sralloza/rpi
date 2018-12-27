import datetime

from rpi import ADMIN_EMAIL
from rpi import operating_system_in_brackets as osib
from rpi.connections import Connections
from rpi.dns import RpiDns
from rpi.exceptions import NeccessaryArgumentError
from rpi.rpi_logging import Logging


def sender_main(resource_id=None, keys=False):
    logger = Logging.get(__file__, __name__)
    automatic = False

    if resource_id is not None:
        if resource_id in (1, 2, 3, 4, 5, 6):
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
        file = {RpiDns.get('textdb.mail-pi'): 'raspberry_mail_pi.txt',
                RpiDns.get('textdb.mail-www-data'): 'raspberry_mail_www_data.txt'}

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

        file = {path + today + '.log': today + '.log.txt'}

    else:
        logger.critical(f'{resource_id} is not a valid resource id')
        raise TypeError(f'{resource_id} is not a valid resource id')

    if file is None:
        logger.critical("'file' argument can't be None")
        raise NeccessaryArgumentError("'file' argument can't be None")

    about += description
    mail_message += about
    mail_message += '</span></h2><p>&nbsp;</p>'

    result_email = Connections.send_email(destino, about, mail_message, files=file, origin='Rpi-Sender')
    if result_email is True:
        # result_notif = Connections.notify('Shipping manager', 'Request accepted:\n' + about, file=__file__)
        logger.debug(f'Shipping Manager {osib()}: sent {description} to {destino}')
    else:
        # result_notif = Connections.notify('Shipping manager', 'Error sending' + description, file=__file__)
        logger.debug(f'Shipping Manager {osib()}: error sending {description} to {destino}')

    # return {'mail': result_email, 'notification': result_notif}
    return {'mail': result_email}