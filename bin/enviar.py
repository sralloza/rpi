# -*- coding: utf-8 -*-

import argparse
import datetime
import time

from rpi import info_plataforma, ADMIN_EMAIL
from rpi.conexiones import Connections
from rpi.dns import RpiDns
from rpi.exceptions import NeccessaryArgumentError
from rpi.rpi_logging import Logger

logger = Logger.get(__file__, __name__)


def _enviar_main(id_recurso=None, keys=False):
    """Inicia el proceso de envío de una base de datos.

    :param id_recurso: indica la ID del archivo a enviar automáticamente.
    :param bool keys: si es true, sólo se imprimen las claves.
    """

    automatic = False
    s = None
    realfilename = None

    if id_recurso is not None:
        if id_recurso in (1, 2, 3, 4, 5, 6):
            s = id_recurso
            automatic = True
            logger.debug('Petición de envío automática: ' + str(id_recurso))

    if keys is True is True:
        print(' 1 |  2   |    3     |   4   |    5   |    6   ')
        print('CV | Logs | Rpi Mail | Menús | Maildb | Log Hoy')
        return

    p = '<h2><span style="color: #339966; font-family: cambria; font-size: 35px;">Petición aceptada: '

    if automatic is False:
        print('\n\n')
        print('--------BASES DE DATOS---------')
        print('1. Historial del Campus Virtual')
        print('2. Logs')
        print('3. Raspberry Mail')
        print('4. Menús de la Residencia')
        print('5. Base de datos de Rpi Mail')
        print('6. Log de hoy ' + datetime.datetime.today().strftime('(%Y-%m-%d)'))
        print('-------------------------------')

        s = int(input('Seleccionar:  '))
        destino = input('Destino: ')
    else:
        destino = ''
    if destino == '':
        destino = ADMIN_EMAIL

    if automatic is False:
        logger.debug(f'Petición de envío manual: {s} a {destino}')

    asunto = 'Enviada '
    if s == 1:
        descripcion = 'Base de datos de links del Campus Virtual de la UVa'
        archivo = RpiDns.get('sqlite.vcs')

    elif s == 2:
        descripcion = 'Logs'
        archivo = RpiDns.get('sqlite.log')

    elif s == 3:
        descripcion = 'Raspberry Mail'
        archivo = [RpiDns.get('textdb.mail-pi'), RpiDns.get('textdb.mail-www-data')]
        realfilename = 'raspberry_mail.txt'

    elif s == 4:
        descripcion = 'Menús Residencia Santiago'
        archivo = RpiDns.get('sqlite.menus_resi')

    elif s == 5:
        descripcion = 'Raspberry Mail Database'
        archivo = RpiDns.get('sqlite.raspberry_mail')

    elif s == 6:
        hoy = datetime.datetime.today().strftime('%Y-%m-%d')
        descripcion = 'Log ' + hoy
        path = RpiDns.get('folder.log')

        if path.endswith('/') is False:
            path += '/'

        archivo = path + hoy + '.log'
        realfilename = hoy + '.log.txt'

    else:
        logger.critical(f'{s} no es una opción válida')
        raise SystemExit(f'{s} no es una opción válida')

    if archivo is None:
        logger.critical('El argumento "archivo" es necesario, no puede ser None.')
        raise NeccessaryArgumentError(f'"archivo" no puede ser None')

    asunto += descripcion
    p += asunto
    p += '</span></h2><p>&nbsp;</p>'
    mail = Connections.send_email(destino, asunto, p, files=archivo, force_file_name=realfilename,
                                  origin='Rpi-Sender')
    if mail is True:
        notif = Connections.notificacion(
            'Gestor de envíos', 'Petición aceptada:\n' + asunto, file=__file__)
        logger.debug('Gestor de envíos ' + info_plataforma() + ': Enviada "' + descripcion + '" a "' + destino + '"')
    else:
        notif = Connections.notificacion(
            'Gestor de envíos', 'Error al enviar "' + descripcion, file=__file__)
        logger.debug(
            'Gestor de envíos ' + info_plataforma() + ': Error al enviar "' + descripcion + '" a "' + destino + '"')

    return {'mail': mail, 'notification': notif}


if __name__ == '__main__':
    t0 = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('id', help='Número de identificación')
    parser.add_argument('-keys', action='store_true',
                        help='Mostrar correspondencias recurso - número de identificación')

    opt = vars(parser.parse_args())

    _enviar_main(id_recurso=opt['id'], keys=opt['keys'])
    logger.debug(f'tiempo de ejecución de enviar: {time.time() - t0:.2f} s')
