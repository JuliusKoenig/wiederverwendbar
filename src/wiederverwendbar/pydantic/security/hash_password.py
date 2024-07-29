import os

import hashlib

from wiederverwendbar.pydantic.security.hashed_password_model import HashedPasswordModel


def hash_password(password: str,
                  encoding: str = "utf-8",
                  hash_function: str = "sha256",
                  interactions: int = 100000,
                  key_length: int = 128,
                  salt: str = None) -> HashedPasswordModel:
    if salt is None:
        salt = os.urandom(32)
        salt = salt.hex()
    salt_encoded = salt.encode(encoding)
    password_encoded = password.encode(encoding)
    hashed_password_encoded = hashlib.pbkdf2_hmac(hash_function, password_encoded, salt_encoded, interactions, key_length)  # generate hash
    hashed_password = hashed_password_encoded.hex()
    out = HashedPasswordModel(
        encoding=encoding,
        hash_function=hash_function,
        interactions=interactions,
        key_length=key_length,
        salt=salt,
        hashed_password=hashed_password
    )
    return out
