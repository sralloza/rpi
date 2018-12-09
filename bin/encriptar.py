import argparse

from cryptography.fernet import InvalidToken

from rpi.cifrado import encrypt_file

parser = argparse.ArgumentParser()
parser.add_argument('file', help="archivo a encriptar")

opt = vars(parser.parse_args())

try:
    encrypt_file(filename=opt['file'])
except FileNotFoundError:
    print(f'Archivo no encontrado: {opt["file"]}')
except InvalidToken:
    print('Error en la operación')
