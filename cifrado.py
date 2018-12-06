from cryptography.fernet import Fernet

from rpi.gestores.gestor_config import GestorConfig


def encrypt(something, key=None):
    fernet = get_fernet(key)
    if isinstance(something, str):
        something = something.encode()

    return fernet.encrypt(something)


def encriptar(something, key=None):
    return encrypt(something, key)


def decrypt(something, key=None):
    fernet = get_fernet(key)
    if isinstance(something, str):
        something = something.encode()
    return fernet.decrypt(something)


def desencriptar(something, key=None):
    return decrypt(something, key)


def get_fernet(key=None):
    if key is None:
        aes_key = GestorConfig.get('aes_key')
    else:
        aes_key = key

    aes_key = aes_key.encode()
    return Fernet(aes_key)


def encrypt_file(filename, key=None):
    fernet = get_fernet(key)

    with open(filename, 'rb') as fh:
        c = fh.read()

    c = fernet.encrypt(c)

    with open(filename, 'wb') as fh:
        fh.write(c)
