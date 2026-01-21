from wiederverwendbar import __author__, __author_email__, __license__, __license_url__, __terms_of_service__
from wiederverwendbar.branding import BrandingSettings
from wiederverwendbar.fastapi import ApiAppSettings
from wiederverwendbar.fastapi.root.settings import RootAppSettings
from wiederverwendbar.logger import LoggerSettings, LogLevels
from wiederverwendbar.nicegui import NiceGUISettings
from wiederverwendbar.printable_settings import PrintableSettings
from wiederverwendbar.uvicorn import UvicornServerSettings

from examples import TEST_ICO


class Settings(PrintableSettings):
    branding: BrandingSettings
    logger: LoggerSettings
    server: UvicornServerSettings
    root: RootAppSettings
    ui: NiceGUISettings
    api: ApiAppSettings


settings = Settings(branding=BrandingSettings(title="Test App",
                                              description="Test Description",
                                              version="0.1.0",
                                              author=__author__,
                                              author_email=__author_email__,
                                              license=__license__,
                                              license_url=__license_url__,
                                              terms_of_service=__terms_of_service__),
                    logger=LoggerSettings(level=LogLevels.DEBUG),
                    server=UvicornServerSettings(),
                    root=RootAppSettings(),
                    ui=NiceGUISettings(),
                    api=ApiAppSettings(docs_favicon=TEST_ICO))
