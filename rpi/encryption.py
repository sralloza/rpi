# -*- coding: utf-8 -*-

"""Encryption functions using Fernet."""
from typing import Union

from cryptography.fernet import Fernet

from rpi.managers.config_manager import ConfigManager


def encrypt(message: Union[str, bytes], key: str = None) -> bytes:
    """Encrypts a message.

    Args:
        message (Union[str, bytes): message to encrypt.
        key (str): fernet key to use.

    Returns:
        bytes: message encrypted.

    """
    fernet = get_fernet(key)
    if isinstance(message, str):
        message = message.encode()

    return fernet.encrypt(message)


def decrypt(message: Union[str, bytes], key: str = None) -> bytes:
    """Decrypts a message

    Args:
        message (Union[str, bytes):message to decrypt.
        key (str): key to use.

    Returns:
        object: message decrypted

    """
    fernet = get_fernet(key)
    if isinstance(message, str):
        message = message.encode()
    return fernet.decrypt(message)


def get_fernet(key: str = None) -> Fernet:
    """Generates a fernet.

    Args:
        key (str): fernet key to use.

    Returns:
         Fernet: fernet instace to encrypt or decrypt.

    """
    if key is None:
        aes_key = ConfigManager.get('aes_key')
    else:
        aes_key = key

    aes_key = aes_key.encode()
    return Fernet(aes_key)


def encrypt_file(filename: str, key: bool = None):
    """

    Args:
        filename (str): path to the file to encrypt.
        key (str): fernet key to encrypt.

    """
    fernet = get_fernet(key)

    with open(filename, 'rb') as file_handler:
        content = file_handler.read()

    content = fernet.encrypt(content)

    with open(filename, 'wb') as file_handler:
        file_handler.write(content)


def decrypt_file(filename: str, key: bool = None):
    """

    Args:
        filename (str): path to the file to decrypt.
        key (str): fernet key to decrypt.

    """
    fernet = get_fernet(key)

    with open(filename, 'rb') as file_handler:
        content = file_handler.read()

    content = fernet.decrypt(content)

    with open(filename, 'wb') as file_handler:
        file_handler.write(content)
