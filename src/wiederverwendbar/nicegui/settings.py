from enum import Enum
from pathlib import Path
from typing import Union

from nicegui.language import Language

from wiederverwendbar.default import Default
from wiederverwendbar.fastapi.root.settings import RootAppSettings
from wiederverwendbar.printable_settings import Field
from wiederverwendbar.pydantic.types.version import Version


class NiceGUISettings(RootAppSettings):
    title: Union[Default, str] = Field(default=Default(), title="Default Page Title", description="Can be overwritten per page.")
    version: Union[Default, Version] = Field(default=Default(), title="FastAPI Version", description="The version of the FastAPI.")
    viewport: Union[Default, str] = Field(default=Default(), title="Default Page meta viewport content", description="Can be overwritten per page.")
    favicon: Union[None, Default, str, Path] = Field(default=Default(), title="Favicon", description="Relative filepath, absolute URL to a favicon or emoji (e.g. '🚀', works for most browsers).")
    dark: Union[None, Default, bool] = Field(default=Default(), title="Dark Mode", description="Whether to use Quasar's dark mode (use None for 'auto' mode).")
    language: Union[Default, Language] = Field(default=Default(), title="Language for Quasar elements", description="Language code, e.g. 'en-US'.")
    binding_refresh_interval: Union[None, Default, float] = Field(default=Default(), title="Binding Refresh Interval", description="Interval for updating active links (bigger is more CPU friendly, can be None to disable update loop).")
    reconnect_timeout: Union[Default, float] = Field(default=Default(), title="Reconnect Timeout", description="Maximum time the server waits for the browser to reconnect.")
    message_history_length: Union[Default, int] = Field(default=Default(), title="Message History Length", description="Maximum number of messages that will be stored and resent after a connection interruption (use 0 to disable).")
    cache_control_directives: Union[Default, str] = Field(default=Default(), title="Cache Control Directives", description="Cache control directives for internal static files.")
    tailwind: Union[Default, bool] = Field(default=Default(), title="Tailwind CSS", description="Whether to use Tailwind CSS (experimental).")
    prod_js: Union[Default, bool] = Field(default=Default(), title="Production JavaScript", description="Whether to use the production version of Vue and Quasar dependencies.")
    storage_secret: Union[None, Default, str] = Field(default=Default(), title="Storage Secret", description="Secret key for browser-based storage (a value is required to enable ui.storage.individual and ui.storage.browser).")
