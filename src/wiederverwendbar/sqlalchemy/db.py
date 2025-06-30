import inspect
import logging
import sqlite3
from ipaddress import IPv4Address
from pathlib import Path
from typing import Any, Optional, Union, Sequence, Callable

from sqlalchemy import create_engine, Table, event
from sqlalchemy.orm import sessionmaker, declarative_base, DeclarativeMeta as _DeclarativeMeta, Session
from sqlalchemy.ext.declarative import declarative_base

from wiederverwendbar.sqlalchemy.settings import SqlalchemySettings

logger = logging.getLogger(__name__)


class DeclarativeMeta(_DeclarativeMeta):
    def __init__(cls, classname: Any, bases: Any, dict_: Any, **kw: Any) -> None:
        db = None
        for base in bases:
            if hasattr(base, "db"):
                db = base.db
        if db is None:
            stack = inspect.stack()
            for frame in stack:
                if frame.function == "__init__":
                    db = frame.frame.f_locals.get("self", None)
                    if isinstance(db, SqlalchemyDb):
                        break
        super().__init__(classname=classname, bases=bases, dict_=dict_, **kw)

        cls.db: SqlalchemyDb = db


class SqlalchemyDb:
    def __init__(self,
                 file: Optional[Path] = None,
                 host: Union[None, IPv4Address, str] = None,
                 port: Optional[int] = None,
                 protocol: Optional[str] = None,
                 name: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 echo: Optional[bool] = None,
                 test_on_startup: Optional[bool] = None,
                 sqlite_check_if_file_exist: Optional[bool] = None,
                 sqlite_handle_foreign_keys: Optional[bool] = None,
                 settings: Optional[SqlalchemySettings] = None):
        """
        Create a new Sqlalchemy Database

        :param host: Host to connect to database
        :param port: Port to connect to database
        :param protocol: Protocol to connect to database
        :param name: Name of the database
        :param username: User to connect to database
        :param password: Password to connect to database
        :param echo: Echo SQL queries to console
        :param test_on_startup: Test the database connection on startup.
        :param sqlite_check_if_file_exist: Check if SQLite file exists before connecting to it.
        :param sqlite_handle_foreign_keys: Enable SQLite Foreign Keys
        :param settings: Sqlalchemy Settings
        """

        self._settings: SqlalchemySettings = settings or SqlalchemySettings()
        self._file: Optional[Path] = file or self.settings.db_file
        self._host: Union[IPv4Address, str, None] = host or self.settings.db_host
        self._port: Optional[int] = port or self.settings.db_port
        self._protocol: Optional[str] = protocol or self.settings.db_protocol
        self._name: Optional[str] = name or self.settings.db_name
        self._username: Optional[str] = username or self.settings.db_username
        self._password: Optional[str] = password or self.settings.db_password
        self._echo: bool = echo or self.settings.db_echo
        self._test_on_startup: bool = test_on_startup or self.settings.db_test_on_startup
        self._sqlite_check_if_file_exist: bool = sqlite_check_if_file_exist or self.settings.db_sqlite_check_if_file_exist
        self._sqlite_handle_foreign_keys: bool = sqlite_handle_foreign_keys or self.settings.db_sqlite_handle_foreign_keys

        logger.debug(f"Create {self}")

        self.engine = create_engine(self.connection_string, echo=self.echo)
        if self.protocol == "sqlite":
            if self.sqlite_check_if_file_exist:
                self.listen("connect", self._sqlite_check_if_file_exist_func)
            if self.sqlite_handle_foreign_keys:
                self.listen("connect", self._sqlite_handle_foreign_keys_func)
        self._session_maker = sessionmaker(bind=self.engine)
        self._Base: DeclarativeMeta = declarative_base(metaclass=DeclarativeMeta)
        self.session_maker.configure(binds={self._Base: self.engine})

        if self.test_on_startup:
            self.test()

    def __str__(self):
        return f"{self.__class__.__name__}({self.connection_string_printable})"

    @property
    def settings(self) -> SqlalchemySettings:
        return self._settings

    @property
    def file(self) -> Optional[Path]:
        return self._file

    @property
    def host(self) -> Union[IPv4Address, str, None]:
        return self._host

    @property
    def port(self) -> Optional[int]:
        return self._port

    @property
    def protocol(self) -> Optional[str]:
        return self._protocol

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def username(self) -> Optional[str]:
        return self._username

    @property
    def password(self) -> Optional[str]:
        return self._password

    @property
    def echo(self) -> bool:
        return self._echo

    @property
    def test_on_startup(self) -> bool:
        return self._test_on_startup

    @property
    def sqlite_check_if_file_exist(self) -> bool:
        return self._sqlite_check_if_file_exist

    @property
    def sqlite_handle_foreign_keys(self) -> bool:
        return self._sqlite_handle_foreign_keys

    @property
    def session_maker(self) -> sessionmaker:
        return self._session_maker

    # noinspection PyPep8Naming
    @property
    def Base(self) -> Any:
        return self._Base

    def get_connection_string(self, printable: bool = False) -> str:
        """
        Get the Connection String

        :param printable: If True, the password will be hidden
        :return: str
        """

        connection_string = f"{self.protocol}://"
        if self.protocol == "sqlite":
            if self.file is not None:
                connection_string += f"/{self.file}"
        else:
            if self.username is not None:
                connection_string += f"{self.username}"
            if self.password is not None:
                connection_string += ":"
                if printable:
                    connection_string += "***"
                else:
                    connection_string += self.password
            if self.host is None:
                raise RuntimeError(f"No host specified for {self.__class__.__name__}")
            connection_string += f"@{self.host}"
            if self.port is None:
                raise RuntimeError(f"No port specified for {self.__class__.__name__}")
            connection_string += f":{self.port}"
            if self.name is None:
                raise RuntimeError(f"No name specified for {self.__class__.__name__}")
            connection_string += f"/{self.name}"
        return connection_string

    @property
    def connection_string(self) -> str:
        """
        Get the Connection String

        :return: str
        """

        return self.get_connection_string()

    @property
    def connection_string_printable(self) -> str:
        """
        Get the Connection String with Password hidden

        :return: str
        """

        return self.get_connection_string(printable=True)

    def test(self):
        self.engine.connect()
        print()

    def create_all(self,
                   tables: Optional[Sequence[Table]] = None,
                   check_first: bool = True) -> None:
        """
        Create all Tables

        :param tables: List of Tables to create. If None, all Tables will be created.
        :param check_first: Check if Tables exist before creating them.
        :return: None
        """

        logger.debug(f"Create all for {self}")
        self.Base.metadata.create_all(bind=self.engine, tables=tables, checkfirst=check_first)

    def session(self) -> Session:
        """
        Create a new Session

        :return: Session
        """

        logger.debug(f"Create Session for {self}")
        return self.session_maker()

    def listen(self,
               identifier: str,
               func: Callable[..., Any],
               *args: Any,
               **kwargs: Any) -> None:
        """
        Register a listener function for the engine.

        :param identifier: String name of the event.
        :param func: Callable function.
        :return: None

        .. Seealso::
            sqlalchemy.event.api.listen for more.
        """

        event.listen(self.engine, identifier, func, *args, **kwargs)

    def listens_for(self,
                    identifier: str,
                    *args: Any,
                    **kw: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Decorate a function as a listener for the engine.

        :param identifier: String name of the event.
        :return: Callable[[Callable[..., Any]], Callable[..., Any]]

        .. Seealso::
            sqlalchemy.event.api.listens_for for more.
        """

        return event.listens_for(self.engine, identifier, *args, **kw)

    def _sqlite_check_if_file_exist_func(self, connection, _connection_record):
        if self.file is not None:
            if not self.file.is_file():
                raise FileNotFoundError(f"Database file does not exist: {self.file}")

    # noinspection PyMethodMayBeStatic
    def _sqlite_handle_foreign_keys_func(self, connection, _connection_record):
        if not isinstance(connection, sqlite3.Connection):
            raise RuntimeError(f"Connection is not a sqlite3.Connection: {connection}")
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
