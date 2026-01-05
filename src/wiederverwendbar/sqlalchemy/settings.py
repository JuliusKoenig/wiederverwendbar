from ipaddress import IPv4Address
from pathlib import Path
from typing import Optional, Union

from wiederverwendbar.printable_settings import PrintableSettings, Field


class SqlalchemySettings(PrintableSettings):
    file: Optional[Path] = Field(default=None, title="Database File", description="File to connect to database")
    host: Union[IPv4Address, str, None] = Field(default=None, title="Database Host", description="Host to connect to database")
    port: Optional[int] = Field(default=None, title="Database Port", ge=0, le=65535, description="Port to connect to database")
    protocol: str = Field(default="sqlite", title="Database Protocol", description="Protocol to connect to database")
    name: Optional[str] = Field(default=None, title="Database Name", description="Name of the database")
    username: Optional[str] = Field(default=None, title="Database User", description="User to connect to database")
    password: Optional[str] = Field(None, title="Database Password", description="Password to connect to database", secret=True)
    echo: bool = Field(default=False, title="Database echo.", description="Echo SQL queries to console")
    test_on_startup: bool = Field(default=True, title="Test Database on Startup", description="Test database connection on startup")
    sqlite_check_if_file_exist: bool = Field(default=True, title="Database SQLite Check If File Exist", description="Check if file exists in SQLite")
    sqlite_handle_foreign_keys: bool = Field(default=True, title="Database SQLite Handle Foreign Keys", description="Handle foreign keys in SQLite")
