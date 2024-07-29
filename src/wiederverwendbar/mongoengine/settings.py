from typing import Optional

from pydantic import BaseModel

from wiederverwendbar.pydantic.printable_settings import Field


class MongoengineSettings(BaseModel):
    db_host: str = Field(default="localhost",
                         title="Database Host",
                         description="Host to connect to database")
    db_port: int = Field(default=27017,
                         title="Database Port",
                         ge=0,
                         le=65535,
                         description="Port to connect to database")
    db_name: str = Field(default=...,
                         title="Database Name",
                         description="Name of the database")
    db_username: Optional[str] = Field(default=None,
                                       title="Database User",
                                       description="User to connect to database")
    db_password: Optional[str] = Field(None,
                                       title="Database Password",
                                       description="Password to connect to database",
                                       secret=True)
    db_timeout: int = Field(default=1000,
                            title="Database Timeout",
                            ge=0,
                            le=60000,
                            description="Timeout to connect to database in milliseconds")
