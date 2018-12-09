import argparse

from cryptography.fernet import InvalidToken

from rpi.cifrado import decrypt_file

parser = argparse.ArgumentParser()
parser.add_argument('file', help="archivo a desencriptar")

opt = vars(parser.parse_args())

try:
    decrypt_file(filename=opt['file'])
except FileNotFoundError:
    print(f'Archivo no encontrado: {opt["file"]}')
except InvalidToken:
    print('Error en la operación')
