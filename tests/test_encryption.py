import os
from pathlib import Path

import pytest

from rpi.encryption import encrypt, decrypt, encrypt_file, decrypt_file


def test_encrypt_decrypt():
    original = 'My name is Will and I will test your code\'s willpower'
    original_encrypted = encrypt(original)

    decrypted = decrypt(original_encrypted).decode()
    assert original == decrypted


def test_encrypt_decrypt_files(tmp_path: Path):
    filename = 'important_message.txt'
    original = 'My name is Will and I will test your code\'s willpower'

    file_path = os.path.join(str(tmp_path), filename)
    with open(file_path, 'w') as fh:
        fh.write(original)

    encrypt_file(file_path)
    decrypt_file(file_path)

    with open(file_path) as fh:
        processed = fh.read()

    assert original == processed


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__), '-v'])
