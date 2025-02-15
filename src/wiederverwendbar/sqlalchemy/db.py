import inspect
import logging
from ipaddress import IPv4Address
from pathlib import Path
from typing import Any, Optional, Union, Sequence

from sqlalchemy import create_engine, Table
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
        :param settings: Sqlalchemy Settings
        """

        self.settings: SqlalchemySettings = settings or SqlalchemySettings()
        self.file: Optional[Path] = file or self.settings.db_file
        self.host: Union[IPv4Address, str, None] = host or self.settings.db_host
        self.port: Optional[int] = port or self.settings.db_port
        self.protocol: Optional[str] = protocol or self.settings.db_protocol
        self.name: Optional[str] = name or self.settings.db_name
        self.username: Optional[str] = username or self.settings.db_username
        self.password: Optional[str] = password or self.settings.db_password
        self.echo: bool = echo or self.settings.db_echo

        logger.debug(f"Create {self}")

        self.engine = create_engine(self.connection_string, echo=self.echo)
        self.session_maker = sessionmaker(bind=self.engine)
        self.Base: DeclarativeMeta = declarative_base(metaclass=DeclarativeMeta)
        self.session_maker.configure(binds={self.Base: self.engine})

    def __str__(self):
        return f"{self.__class__.__name__}({self.connection_string_printable})"

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
                raise RuntimeError(f"No host specified for {self}")
            connection_string += f"@{self.host}"
            if self.port is None:
                raise RuntimeError(f"No port specified for {self}")
            connection_string += f":{self.port}"
            if self.name is None:
                raise RuntimeError(f"No name specified for {self}")
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
