from datetime import datetime

from mongoengine import EmbeddedDocument, StringField, IntField, DateTimeField
from wiederverwendbar.functions.security.hashed_password import HashedPassword


class HashedPasswordDocument(EmbeddedDocument, HashedPassword):
    meta = {"allow_inheritance": True}

    encoding: str = StringField(required=True)
    hash_function: str = StringField(required=True)
    interactions: int = IntField(required=True)
    key_length: int = IntField(required=True)
    salt: str = StringField(required=True)
    hashed_password: str = StringField(required=True)
