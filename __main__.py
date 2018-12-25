# -*- coding: utf-8 -*-

import argparse
import sys

from . import __VERSION__ as VERSION, ADMIN_EMAIL
from .connections import Connections
from .managers.user_manager import UserManager


def report_error(error):
    Connections.send_email(ADMIN_EMAIL, 'ERROR REPORTADO', error, origin='RpiWeb Error Reporter')


def main():
    if len(sys.argv) <= 1:
        sys.argv.append('-h')

    gu = UserManager()

    parser = argparse.ArgumentParser(description='Rpi', prog='rpi')

    parser.add_argument('-version', help='ver versión', action='store_true')

    subparser = parser.add_subparsers()

    usuarios_parser = subparser.add_parser('usuarios')

    usuarios_parser.add_argument('-ver', help='ver usuarios', action='store_true')
    usuarios_parser.add_argument('-usernames', help='ver usernames', action='store_true')

    notificar = subparser.add_parser('notificar')
    notificar.add_argument('titulo')
    notificar.add_argument('mensaje')
    notificar.add_argument('destinos', nargs='+', choices=gu.usernames)

    email = subparser.add_parser('email')
    email.add_argument('destino')
    email.add_argument('asunto')
    email.add_argument('mensaje')
    email.add_argument('-archivo')

    opt = vars(parser.parse_args())

    if 'version' in opt:
        if opt['version'] is True:
            print(f'rpi {VERSION}')
            return

    try:
        if opt['ver'] is False and opt['eliminar'] is None and opt['usernames'] is False:
            print(gu.usernames)
            return
    except KeyError:
        pass

    if 'ver' in opt:
        if opt['ver'] is True:
            print(gu)
            return

    if 'usernames' in opt:
        if opt['usernames'] is True:
            print(gu.usernames)
            return

    if 'titulo' in opt:
        Connections.DISABLE = False
        if Connections.notify(opt['titulo'], opt['mensaje'], opt['destinos'], force=True) is False:
            print('Error en notificación')
        else:
            print('Notifiación enviada con éxito')


#

if __name__ == '__main__':
    main()
