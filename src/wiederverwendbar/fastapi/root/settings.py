from typing import Union

from wiederverwendbar.default import Default
from wiederverwendbar.printable_settings import PrintableSettings, Field


class RootAppSettings(PrintableSettings):
    debug: Union[Default, bool] = Field(default=Default(), title="FastAPI Debug", description="Whether the FastAPI is in debug mode.")
    root_path: Union[Default, str] = Field(default=Default(), title="FastAPI Root Path", description="The root path of the FastAPI.")
    root_path_in_servers: Union[Default, bool] = Field(default=Default(), title="FastAPI Root Path in Servers", description="Whether the root path of the FastAPI is in servers.")
    root_redirect: Union[None, Default, str] = Field(default=Default(), title="FastAPI Root Redirect", description="The root redirect of the FastAPI.")
