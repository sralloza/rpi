# -*- coding: utf-8 -*-

import argparse
import sys

from .conexiones import Conexiones
from .exceptions import UnrecognisedUsernameError
from .gestor_usuarios import rpi_gu
from . import __VERSION__ as version

def main():
    if len(sys.argv) <= 1:
        sys.argv.append('-h')

    parser = argparse.ArgumentParser(description='Rpi', prog='rpi')

    parser.add_argument('-version', help='ver versión', action='store_true')

    subparser = parser.add_subparsers()

    usuarios_parser = subparser.add_parser('usuarios')

    usuarios_parser.add_argument('-eliminar', help='eliminar usuario')
    usuarios_parser.add_argument('-ver', help='ver usuarios', action='store_true')
    usuarios_parser.add_argument('-usernames', help='ver usernames', action='store_true')

    notificar = subparser.add_parser('notificar')
    notificar.add_argument('titulo')
    notificar.add_argument('mensaje')
    notificar.add_argument('destinos', nargs='+', choices=rpi_gu.usernames)

    email = subparser.add_parser('email')
    email.add_argument('destino')
    email.add_argument('asunto')
    email.add_argument('mensaje')
    email.add_argument('-archivo')

    opt = vars(parser.parse_args())

    if 'version' in opt:
        if opt['version'] is True:
            print(f'rpi {version}')
            return

    try:
        if opt['ver'] is False and opt['eliminar'] is None and opt['usernames'] is False:
            print(rpi_gu.usernames)
            return
    except KeyError:
        pass

    if 'ver' in opt:
        if opt['ver'] is True:
            print(rpi_gu)
            return

    if 'usernames' in opt:
        if opt['usernames'] is True:
            print(rpi_gu.usernames)
            return

    if 'eliminar' in opt:
        try:
            rpi_gu.delete(opt['eliminar'])
            rpi_gu.save()
        except UnrecognisedUsernameError as err:
            print(err)
        else:
            print(f"Usuario '{opt['eliminar']}' eliminado correctamente")
        return

    if 'titulo' in opt:
        Conexiones.DISABLE = False
        if Conexiones.notificacion(opt['titulo'], opt['mensaje'], opt['destinos'], _forzar_notificacion=True) is False:
            print('Error en notificación')
        else:
            print('Notifiación enviada con éxito')


#

if __name__ == '__main__':
    main()
