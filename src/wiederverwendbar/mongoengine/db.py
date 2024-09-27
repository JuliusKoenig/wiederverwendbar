import logging
from pathlib import Path
from typing import Optional, Union
from ipaddress import IPv4Address

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError
from mongoengine import DEFAULT_CONNECTION_NAME, connect, disconnect

from wiederverwendbar.mongoengine.backup import dump, restore
from wiederverwendbar.mongoengine.settings import MongoengineSettings

logger = logging.getLogger(__name__)


class MongoengineDb:
    def __init__(self,
                 name: Optional[str] = None,
                 host: Union[None, IPv4Address, str] = None,
                 port: Optional[int] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 auth_source: Optional[str] = None,
                 timeout: Optional[int] = None,
                 test: Optional[bool] = None,
                 auto_connect: Optional[bool] = None,
                 settings: Optional[MongoengineSettings] = None):
        """
        Create a new Mongoengine Database

        :param name: Database Name(aka Alias in Mongoengine)
        :param settings: Mongoengine Settings
        """

        self.name: str = name or DEFAULT_CONNECTION_NAME
        self.settings: MongoengineSettings = settings or MongoengineSettings()
        self.host: Union[IPv4Address, str] = host or self.settings.db_host
        self.port: int = port or self.settings.db_port
        self.db_name: str = name or self.settings.db_name
        self.username: str = username or self.settings.db_username
        self.password: str = password or self.settings.db_password
        self.auth_source: str = auth_source or self.settings.db_auth_source
        self.timeout: int = timeout or self.settings.db_timeout
        self.db_test: bool = test or self.settings.db_test
        self.auto_connect: bool = auto_connect or self.settings.db_auto_connect

        logger.debug(f"Create {self}")

        # connect to database
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None

        if self.auto_connect:
            self.connect()

    def __str__(self):
        return f"{self.__class__.__name__}(name={self.name}, host={self.host}, port={self.port})"

    def __del__(self):
        if self.is_connected:
            self.disconnect()

    @property
    def connection_string(self) -> str:
        """
        Get the Connection String

        :return: str
        """

        connection_string = "mongodb://"
        if self.username and self.password:
            connection_string += f"{self.username}:{self.password}@"
        connection_string += f"{self.host}:{self.port}/{self.db_name}?authSource={self.auth_source}"

        return connection_string

    @property
    def client(self) -> MongoClient:
        """
        Get the Database Client

        :return: MongoClient
        """

        if self._client is None:
            self.connect()
        return self._client

    @property
    def db(self) -> Database:
        """
        Get the Database

        :return: Database
        """

        if self._db is None:
            self.connect()
        return self._db

    @property
    def is_connected(self) -> bool:
        """
        Check if the database is connected

        :return: bool
        """

        if self._client is None:
            return False
        if self._db is None:
            return False
        return True

    def connect(self) -> None:
        """
        Connect to the database

        :return: None
        """

        logger.debug(f"Connect to {self} ...")

        if self.is_connected:
            raise RuntimeError(f"Already connected to {self}")

        self._client = connect(db=self.db_name,
                               alias=self.name,
                               host=self.host,
                               port=self.port,
                               username=self.username,
                               password=self.password,
                               authSource=self.auth_source,
                               serverSelectionTimeoutMS=self.timeout)
        self._db = self.client[self.db_name]

        if self.db_test:
            self.test()

    def test(self):
        """
        Test the database connection

        :return: None
        """

        logger.debug(f"Testing {self} ...")

        if not self.is_connected:
            raise RuntimeError(f"Not connected to {self}")

        try:
            self.db.list_collection_names()
        except PyMongoError as e:
            raise RuntimeError(f"Could not connect to database: {e}")

    def disconnect(self) -> None:
        """
        Disconnect from the database

        :return: None
        """

        logger.debug(f"Disconnect from {self} ...")

        if not self.is_connected:
            raise RuntimeError(f"Not connected to {self}")

        disconnect(alias=self.name)
        self._client = None
        self._db = None

    def dump(self: Database, path: Union[str, Path], overwrite: bool = False) -> None:
        """
        MongoDB Dump
        :param path: Database dump path
        :param overwrite: Overwrite existing files
        :return: None
        """

        dump(db=self.db, path=path, overwrite=overwrite)

    def restore(self: Database, path: Union[str, Path], overwrite: bool = False) -> None:
        """
        MongoDB Restore
        :param path: Database dump path
        :param overwrite: Overwrite existing collections
        :return: None
        """

        restore(db=self.db, path=path, overwrite=overwrite)
