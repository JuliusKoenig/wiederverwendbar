from typer_example.sub import sub_app

from wiederverwendbar import __author__, __author_email__, __license__, __license_url__, __terms_of_service__
from wiederverwendbar.branding import BrandingSettings
from wiederverwendbar.logger import LoggerSettings, LogLevels, LoggerSingleton
from wiederverwendbar.printable_settings import PrintableSettings
from wiederverwendbar.rich import RichConsoleSettings
from wiederverwendbar.typer import Typer, TyperSettings


class MySettings(PrintableSettings):
    branding: BrandingSettings
    logger: LoggerSettings
    cli: TyperSettings
    console: RichConsoleSettings


settings = MySettings(branding=BrandingSettings(title="Test App",
                                                description="Test Description",
                                                version="0.1.0",
                                                author=__author__,
                                                author_email=__author_email__,
                                                license=__license__,
                                                license_url=__license_url__,
                                                terms_of_service=__terms_of_service__),
                      logger=LoggerSettings(log_level=LogLevels.DEBUG),
                      cli=TyperSettings(),
                      console=RichConsoleSettings())

LoggerSingleton(name=__name__, settings=settings.logger, init=True)  # ToDo fix this unresolved attr

app = Typer(settings=settings.cli,
            branding_settings=settings.branding,
            console_settings=settings.console)


@app.command()
def test1():
    app.console.print("test1")


@app.command()
def test2():
    app.console.print("test2")


app.add_typer(sub_app, name="sub")

if __name__ == "__main__":
    app()
