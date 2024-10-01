import logging

from mongoengine import StringField

from wiederverwendbar.mongoengine import MongoengineDbSingleton, MongoengineLogDocument, MongoengineLogHandler

MongoengineDbSingleton(init=True)


class MyMongoengineLogDocument(MongoengineLogDocument):
    meta = {"collection": "log.test"}

    test = StringField(required=True)


logger = logging.getLogger("test123")

logger.addHandler(logging.StreamHandler())
logger.addHandler(MongoengineLogHandler(document=MyMongoengineLogDocument, document_kwargs={"test": "test"}))

logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    logger.debug("Hello")
    logger.debug("Hello")
