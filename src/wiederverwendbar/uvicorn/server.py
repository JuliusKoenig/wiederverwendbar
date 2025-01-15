import logging
import os
from ipaddress import IPv4Address
from typing import Callable, Any, Union, Optional

import uvicorn
from uvicorn._types import ASGIApplication

from wiederverwendbar.uvicorn.settings import UvicornServerSettings

logger = logging.getLogger(__name__)


class UvicornServer:
    def __init__(self,
                 app: Union[ASGIApplication, Callable[..., Any], str],
                 host: Union[None, IPv4Address, str] = None,
                 port: Optional[int] = None,
                 reload: Optional[bool] = False,
                 reload_dirs: Union[list[str], str, None] = None,
                 reload_includes: Union[list[str], str, None] = None,
                 reload_excludes: Union[list[str], str, None] = None,
                 reload_delay: Optional[float] = None,
                 workers: Optional[int] = None,
                 ssl_keyfile: Optional[str] = None,
                 ssl_certfile: Union[str, os.PathLike[str], None] = None,
                 ssl_keyfile_password: Optional[str] = None,
                 ssl_version: Optional[int] = None,
                 ssl_cert_reqs: Optional[int] = None,
                 ssl_ca_certs: Optional[str] = None,
                 ssl_ciphers: Optional[str] = None,
                 auto_run: bool = True,
                 server_react_to_keyboard_interrupt: bool = True,
                 factory: bool = False,
                 settings: Optional[UvicornServerSettings] = None):
        """
        Create a new Uvicorn Server

        :param app: ASGI Application
        :param host: Host to bind to
        :param port: Port to bind to
        :param reload: Enable auto-reload
        :param reload_dirs: Reload Directories
        :param reload_includes: Reload Includes
        :param reload_excludes: Reload Excludes
        :param reload_delay: Reload Delay
        :param workers: Number of worker processes
        :param ssl_keyfile: SSL Keyfile
        :param ssl_certfile: SSL Certfile
        :param ssl_keyfile_password: SSL Keyfile Password
        :param ssl_version: SSL Version
        :param ssl_cert_reqs: SSL Cert Reqs
        :param ssl_ca_certs: SSL CA Certs
        :param ssl_ciphers: SSL Ciphers
        :param auto_run: Auto Run on creation
        :param server_react_to_keyboard_interrupt: React to Keyboard Interrupt
        :param factory: Factory
        :param settings: Uvicorn Server Settings
        """

        self.app = app
        self.settings = settings or UvicornServerSettings()

        self.host: IPv4Address = host or self.settings.server_host
        self.port: int = port or self.settings.server_port
        self.reload: bool = reload or self.settings.server_reload
        self.reload_dirs: Union[list[str], str, None] = reload_dirs or self.settings.server_reload_dirs
        self.reload_includes: Union[list[str], str, None] = reload_includes or self.settings.server_reload_includes
        self.reload_excludes: Union[list[str], str, None] = reload_excludes or self.settings.server_reload_excludes
        self.reload_delay: float = reload_delay or self.settings.server_reload_delay
        self.workers: int = workers or self.settings.server_workers
        ssl_keyfile = ssl_keyfile or self.settings.server_ssl_keyfile
        if ssl_keyfile:
            ssl_keyfile = str(ssl_keyfile)
        ssl_certfile = ssl_certfile or self.settings.server_ssl_certfile
        if ssl_certfile:
            ssl_certfile = str(ssl_certfile)
        self.ssl_keyfile: Optional[str] = ssl_keyfile
        self.ssl_certfile: Optional[str] = ssl_certfile
        self.ssl_keyfile_password: Optional[str] = ssl_keyfile_password or self.settings.server_ssl_keyfile_password
        self.ssl_version: int = ssl_version or self.settings.server_ssl_version
        self.ssl_cert_reqs: int = ssl_cert_reqs or self.settings.server_ssl_cert_reqs
        self.ssl_ca_certs: Optional[str] = str(ssl_ca_certs or self.settings.server_ssl_ca_certs)
        self.ssl_ciphers: Optional[str] = ssl_ciphers or self.settings.server_ssl_ciphers
        self.auto_run: bool = auto_run
        self.react_to_keyboard_interrupt = server_react_to_keyboard_interrupt
        self.factory: bool = factory

        logger.debug(f"Create {self}")

        if self.auto_run:
            self.run()

    def __str__(self):
        return f"{self.__class__.__name__}(host={self.host}, port={self.port})"

    def run(self) -> None:
        """
        Run the Uvicorn Server

        :return: None
        """

        logger.info(f"Run {self}")
        if not self.react_to_keyboard_interrupt:
            self._run()
        else:
            try:
                self._run()
            except KeyboardInterrupt:
                logger.info(f"Keyboard Interrupt {self}")
        logger.info(f"Stop {self}")

    def _run(self):
        uvicorn.run(self.app,
                    host=str(self.host),
                    port=self.port,
                    reload=self.reload,
                    reload_dirs=self.reload_dirs,
                    reload_includes=self.reload_includes,
                    reload_excludes=self.reload_excludes,
                    reload_delay=self.reload_delay,
                    workers=self.workers,
                    ssl_keyfile=self.ssl_keyfile,
                    ssl_certfile=self.ssl_certfile,
                    ssl_keyfile_password=self.ssl_keyfile_password,
                    ssl_version=self.ssl_version,
                    ssl_cert_reqs=self.ssl_cert_reqs,
                    ssl_ca_certs=self.ssl_ca_certs,
                    ssl_ciphers=self.ssl_ciphers,
                    factory=self.factory)
