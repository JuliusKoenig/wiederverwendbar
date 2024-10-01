from datetime import datetime

from mongoengine import Document, DateTimeField, StringField, ListField, DictField
from mongoengine.base import TopLevelDocumentMetaclass


class MongoengineLogDocumentMeta(TopLevelDocumentMetaclass):
    ...

class MongoengineLogDocument(Document, metaclass=MongoengineLogDocumentMeta):
    meta = {"collection": "log",
            "allow_inheritance": True}

    name: str = StringField(required=True)
    timestamp: datetime = DateTimeField(required=True)
    entries: list[dict] = ListField(DictField(), required=True)
