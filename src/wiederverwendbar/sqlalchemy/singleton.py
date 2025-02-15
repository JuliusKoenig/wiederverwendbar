from wiederverwendbar.sqlalchemy.db import SqlalchemyDb
from wiederverwendbar.singleton import Singleton


class SqlalchemyDbSingleton(SqlalchemyDb, metaclass=Singleton):
    ...
