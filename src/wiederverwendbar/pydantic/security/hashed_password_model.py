from pydantic import BaseModel


class HashedPasswordModel(BaseModel):
    encoding: str
    hash_function: str
    interactions: int
    key_length: int
    salt: str
    hashed_password: str
