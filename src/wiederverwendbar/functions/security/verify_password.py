from wiederverwendbar.pydantic.security.hashed_password_model import HashedPasswordModel
from wiederverwendbar.functions.security.hash_password import hash_password


def verify_password(hashed_password_model: HashedPasswordModel, verifying_password: str) -> bool:
    hashed_verify_password = hash_password(
        password=verifying_password,
        encoding=hashed_password_model.encoding,
        hash_function=hashed_password_model.hash_function,
        interactions=hashed_password_model.interactions,
        key_length=hashed_password_model.key_length,
        salt=hashed_password_model.salt
    )
    result = hashed_password_model.hashed_password == hashed_verify_password.hashed_password
    return result
