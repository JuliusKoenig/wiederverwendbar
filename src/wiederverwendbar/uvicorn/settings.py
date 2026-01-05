import ssl
from ipaddress import IPv4Address
from typing import Union, Optional

from pydantic import FilePath
from uvicorn.config import SSL_PROTOCOL_VERSION

from wiederverwendbar.printable_settings import PrintableSettings, Field


class UvicornServerSettings(PrintableSettings):
    host: Union[IPv4Address, str] = Field(default=IPv4Address("127.0.0.1"), title="Server Host", description="Server Host to bind to")
    port: int = Field(default=8000, title="Server Port", ge=0, le=65535, description="Server Port to bind to")
    reload: bool = Field(default=False, title="Server Reload", description="Server Enable auto-reload")
    reload_dirs: Union[None, list[str], str] = Field(default=None, title="Server Reload Dirs", description="Server Directories to watch for changes")
    reload_includes: Union[None, list[str], str] = Field(default=None, title="Server Reload Includes", description="File patterns to include")
    reload_excludes: Union[None, list[str], str] = Field(default=None, title="Server Reload Excludes", description="File patterns to exclude")
    reload_delay: float = Field(default=0.25, title="Server Reload Delay", ge=0.1, description="Server Delay between reloads")
    workers: int = Field(default=1, title="Server Workers", ge=1, le=100, description="Server Number of worker processes")
    ssl_keyfile: Optional[FilePath] = Field(default=None, title="Server SSL Keyfile", description="Server SSL Keyfile")
    ssl_certfile: Optional[FilePath] = Field(default=None, title="Server SSL Certfile", description="Server SSL Certfile")
    ssl_keyfile_password: Optional[str] = Field(default=None, title="Server SSL Keyfile Password", description="Server SSL Keyfile Password")
    ssl_version: int = Field(default=SSL_PROTOCOL_VERSION, title="Server SSL Version", description="Server SSL Version")
    ssl_cert_reqs: int = Field(default=ssl.CERT_NONE, title="Server SSL Cert Reqs", description="Server SSL Cert Reqs")
    ssl_ca_certs: Optional[FilePath] = Field(default=None, title="Server SSL CA Certs", description="Server SSL CA Certs")
    ssl_ciphers: str = Field(default="TLSv1", title="Server SSL Ciphers", description="Server SSL Ciphers")
