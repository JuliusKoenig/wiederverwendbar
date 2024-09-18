from wiederverwendbar.mongoengine.db import MongoengineDb
from wiederverwendbar.singleton import Singleton


class MongoengineDbSingleton(MongoengineDb, metaclass=Singleton):
    ...
