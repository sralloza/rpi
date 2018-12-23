from cryptography.fernet import Fernet

from rpi.managers.config_manager import GestorConfig


def encrypt(anything, key=None):
    fernet = get_fernet(key)
    if isinstance(anything, str):
        anything = anything.encode()

    return fernet.encrypt(anything)


def decrypt(anything, key=None):
    fernet = get_fernet(key)
    if isinstance(anything, str):
        anything = anything.encode()
    return fernet.decrypt(anything)


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


def decrypt_file(filename, key=None):
    fernet = get_fernet(key)

    with open(filename, 'rb') as fh:
        c = fh.read()

    c = fernet.decrypt(c)

    with open(filename, 'wb') as fh:
        fh.write(c)
