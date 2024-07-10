from mongoengine import EmbeddedDocument, StringField, IntField


class HashedPasswordDocument(EmbeddedDocument):
    encoding = StringField()
    hash_function = StringField()
    interactions = IntField()
    key_length = IntField()
    salt = StringField()
    hashed_password = StringField()
