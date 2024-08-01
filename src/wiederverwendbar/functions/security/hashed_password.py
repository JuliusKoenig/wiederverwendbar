import os
import hashlib
from typing import Any, Optional

ENCODING = "utf-8"
HASH_FUNCTION = "sha256"
INTERACTIONS = 100000
KEY_LENGTH = 128
SALT_LENGTH = 32


def hash_password(password: str,
                  encoding: Optional[str] = None,
                  hash_function: Optional[str] = None,
                  interactions: Optional[int] = None,
                  key_length: Optional[int] = None,
                  salt: Optional[str] = None) -> dict[str, Any]:
    encoding = encoding or ENCODING
    hash_function = hash_function or HASH_FUNCTION
    interactions = interactions or INTERACTIONS
    key_length = key_length or KEY_LENGTH
    salt = salt or os.urandom(SALT_LENGTH).hex()

    salt_encoded = salt.encode(encoding)
    password_encoded = password.encode(encoding)
    hashed_password_encoded = hashlib.pbkdf2_hmac(hash_function, password_encoded, salt_encoded, interactions, key_length)  # generate hash
    hashed_password = hashed_password_encoded.hex()
    out = {
        "encoding": encoding,
        "hash_function": hash_function,
        "interactions": interactions,
        "key_length": key_length,
        "salt": salt,
        "hashed_password": hashed_password
    }
    return out


def verify_password(hashed_password: dict[str, Any], verifying_password: str) -> bool:
    hashed_verify_password = hash_password(
        password=verifying_password,
        encoding=hashed_password["encoding"],
        hash_function=hashed_password["hash_function"],
        interactions=hashed_password["interactions"],
        key_length=hashed_password["key_length"],
        salt=hashed_password["salt"]
    )
    result = hashed_password["hashed_password"] == hashed_verify_password["hashed_password"]
    return result


class HashedPassword:
    def __init__(self,
                 encoding: str,
                 hash_function: str,
                 interactions: int,
                 key_length: int,
                 salt: str,
                 hashed_password: str):
        self.encoding = encoding
        self.hash_function = hash_function
        self.interactions = interactions
        self.key_length = key_length
        self.salt = salt
        self.hashed_password = hashed_password

    @classmethod
    def hash_password(cls,
                      password: str,
                      encoding: Optional[str] = None,
                      hash_function: Optional[str] = None,
                      interactions: Optional[int] = None,
                      key_length: Optional[int] = None,
                      salt: Optional[str] = None) -> Any:
        # create hashed password dict
        hashed_password = hash_password(
            password=password,
            encoding=encoding,
            hash_function=hash_function,
            interactions=interactions,
            key_length=key_length,
            salt=salt
        )

        # create hashed password object
        hashed_password_obj = cls(**hashed_password)

        return hashed_password_obj

    def verify_password(self, verifying_password: str) -> bool:
        hashed_password = {
            "encoding": self.encoding,
            "hash_function": self.hash_function,
            "interactions": self.interactions,
            "key_length": self.key_length,
            "salt": self.salt,
            "hashed_password": self.hashed_password
        }
        result = verify_password(hashed_password, verifying_password)
        return result
