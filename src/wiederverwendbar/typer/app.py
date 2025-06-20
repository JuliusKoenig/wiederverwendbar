import inspect
from typing import Optional, Annotated, Union

from typer import Typer as _Typer, Option, Exit
from art import text2art

from wiederverwendbar.default import Default
from wiederverwendbar.rich.console import RichConsole
from wiederverwendbar.typer.settings import TyperSettings


class Typer(_Typer):
    def __init__(self,
                 *,
                 title: Union[Default, str] = Default(),
                 description: Union[None, Default, str] = Default(),
                 version: Union[Default, str] = Default(),
                 author: Union[None, Default, str] = Default(),
                 author_email: Union[None, Default, str] = Default(),
                 license: Union[None, Default, str] = Default(),
                 license_url: Union[None, Default, str] = Default(),
                 terms_of_service: Union[None, Default, str] = Default(),
                 info_enabled: Union[Default, bool] = Default(),
                 version_enabled: Union[Default, bool] = Default(),
                 name: Union[None, Default, str] = Default(),
                 help: Union[None, Default, str] = Default(),
                 settings: Optional[TyperSettings] = None,
                 console: Optional[RichConsole] = None,
                 main_callback_parameters: Optional[list[inspect.Parameter]] = None,
                 **kwargs):

        # set default
        if settings is None:
            settings = TyperSettings()
        if type(title) is Default:
            title = settings.branding_title
        if title is None:
            title = "Typer"
        if type(description) is Default:
            description = settings.branding_description
        if type(version) is Default:
            version = settings.branding_version
        if version is None:
            version = "0.1.0"
        if type(author) is Default:
            author = settings.branding_author
        if type(author_email) is Default:
            author_email = settings.branding_author_email
        if type(license) is Default:
            license = settings.branding_license
        if type(license_url) is Default:
            license_url = settings.branding_license_url
        if type(terms_of_service) is Default:
            terms_of_service = settings.branding_terms_of_service
        if type(info_enabled) is Default:
            info_enabled = settings.cli_info_enabled
        if type(version_enabled) is Default:
            version_enabled = settings.cli_version_enabled
        if type(name) is Default:
            name = settings.cli_name
        if type(name) is Default:
            name = title
        if type(help) is Default:
            help = settings.cli_help
        if type(help) is Default:
            help = description
        if console is None:
            console = RichConsole(settings=settings)
        if main_callback_parameters is None:
            main_callback_parameters = []

        super().__init__(name=name, help=help, **kwargs)

        # set attrs
        self.title = title
        self.description = description
        self.version = version
        self.author = author
        self.author_email = author_email
        self.license = license
        self.license_url = license_url
        self.terms_of_service = terms_of_service
        self.info_enabled = info_enabled
        self.version_enabled = version_enabled
        self.name = name
        self.help = help
        self.console = console

        # add info command parameter to main_callback_parameters
        if info_enabled:
            def info_callback(value: bool) -> None:
                if not value:
                    return
                code = self.info_command()
                if code is None:
                    code = 0
                raise Exit(code=code)

            main_callback_parameters.append(inspect.Parameter(name="info",
                                                              kind=inspect.Parameter.KEYWORD_ONLY,
                                                              default=False,
                                                              annotation=Annotated[Optional[bool], Option("--info",
                                                                                                          help="Show information of the application.",
                                                                                                          callback=info_callback)]))

        # add version command parameter to main_callback_parameters
        if version_enabled:
            def version_callback(value: bool):
                if not value:
                    return
                code = self.version_command()
                if code is None:
                    code = 0
                raise Exit(code=code)

            main_callback_parameters.append(inspect.Parameter(name="version",
                                                              kind=inspect.Parameter.KEYWORD_ONLY,
                                                              default=False,
                                                              annotation=Annotated[Optional[bool], Option("-v",
                                                                                                          "--version",
                                                                                                          help="Show version of the application.",
                                                                                                          callback=version_callback)]))

        # backup main callback
        orig_main_callback = self.main_callback

        def main_callback(*a, **kw):
            orig_main_callback(*a, **kw)

        # update signature
        main_callback.__signature__ = inspect.signature(self.main_callback).replace(parameters=main_callback_parameters)

        # overwrite the main callback
        self.main_callback = main_callback

        # register the main callback
        self.callback()(self.main_callback)

    @property
    def title_header(self) -> str:
        return text2art(self.title)

    def main_callback(self, *args, **kwargs):
        ...

    def info_command(self) -> Optional[int]:
        card_body = [self.title_header]
        second_section = ""
        if self.description is not None:
            second_section += f"{self.description}"
        if self.author is not None:
            if second_section != "":
                second_section += "\n"
            second_section += f"by {self.author}"
            if self.author_email is not None:
                second_section += f" ({self.author_email})"
        if second_section != "":
            second_section += "\n"
        second_section += f"Version: v{self.version}"
        if self.license is not None:
            second_section += f"\nLicense: {self.license}"
            if self.license_url is not None:
                second_section += f" - {self.license_url}"
        if self.terms_of_service is not None:
            second_section += f"\nTerms of Service: {self.terms_of_service}"
        card_body.append(second_section)

        self.console.card(*card_body,
                          padding_left=1,
                          padding_right=1,
                          border_style="double_line",
                          color="white",
                          border_color="blue")

    def version_command(self) -> Optional[int]:
        self.console.print(f"{self.title} v[cyan]{self.version}[/cyan]")
