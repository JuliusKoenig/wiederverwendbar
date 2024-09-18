import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError
from mongoengine import DEFAULT_CONNECTION_NAME, connect, disconnect

from wiederverwendbar.mongoengine.settings import MongoengineSettings

logger = logging.getLogger(__name__)


class MongoengineDb:
    def __init__(self, name: Optional[str] = None, settings: Optional[MongoengineSettings] = None):
        """
        Create a new Mongoengine Database

        :param name: Database Name(aka Alias in Mongoengine)
        :param settings: Mongoengine Settings
        """

        self.name = name or DEFAULT_CONNECTION_NAME
        self.settings = settings or MongoengineSettings()

        self.host = self.settings.db_host
        self.port = self.settings.db_port
        self.name = self.settings.db_name
        self.username = self.settings.db_username
        self.password = self.settings.db_password
        self.auth_source = self.settings.db_auth_source
        self.timeout = self.settings.db_timeout
        self.test = self.settings.db_test
        self.auto_connect = self.settings.db_auto_connect

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

        self._client = connect(alias=self.name,
                               host=self.host,
                               port=self.port,
                               username=self.username,
                               password=self.password,
                               authSource=self.auth_source,
                               serverSelectionTimeoutMS=self.timeout)
        self._db = self.client[self.name]

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
