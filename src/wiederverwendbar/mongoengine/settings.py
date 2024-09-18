from typing import Optional, Union
from ipaddress import IPv4Address

from wiederverwendbar.pydantic.printable_settings import PrintableSettings, Field


class MongoengineSettings(PrintableSettings):
    db_host: Union[IPv4Address, str] = Field(default="127.0.0.1",
                                             title="Database Host",
                                             description="Host to connect to database")
    db_port: int = Field(default=27017,
                         title="Database Port",
                         ge=0,
                         le=65535,
                         description="Port to connect to database")
    db_name: str = Field(default="test",
                         title="Database Name",
                         description="Name of the database")
    db_username: Optional[str] = Field(default=None,
                                       title="Database User",
                                       description="User to connect to database")
    db_password: Optional[str] = Field(None,
                                       title="Database Password",
                                       description="Password to connect to database",
                                       secret=True)
    db_auth_source: str = Field(default="admin",
                                title="Database Auth Source",
                                description="Auth source to connect to database")
    db_timeout: int = Field(default=1000,
                            title="Database Timeout",
                            ge=0,
                            le=60000,
                            description="Timeout to connect to database in milliseconds")
    db_test: bool = Field(default=False,
                          title="Database Test",
                          description="Test database connection on connect")
    db_auto_connect: bool = Field(default=True,
                                  title="Database Auto Connect",
                                  description="Auto connect to database on startup")
