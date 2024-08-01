from pydantic import BaseModel, Field
from wiederverwendbar.functions.security.hashed_password import HashedPassword


class HashedPasswordModel(BaseModel, HashedPassword):
    encoding: str = Field(..., title="Encoding", description="The encoding of the hashed password.")
    hash_function: str = Field(..., title="Hash Function", description="The hash function of the hashed password.")
    interactions: int = Field(..., title="Interactions", description="The interactions of the hashed password.")
    key_length: int = Field(..., title="Key Length", description="The key length of the hashed password.")
    salt: str = Field(..., title="Salt", description="The salt of the hashed password.")
    hashed_password: str = Field(..., title="Hashed Password", description="The hashed password.")
