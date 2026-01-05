import inspect
from typing import Optional, Annotated, Union

from typer import Typer as _Typer, Option, Exit
from art import text2art

from wiederverwendbar.branding.settings import BrandingSettings
from wiederverwendbar.default import Default
from wiederverwendbar.pydantic.types.version import Version
from wiederverwendbar.rich.settings import RichConsoleSettings
from wiederverwendbar.rich.console import RichConsole
from wiederverwendbar.typer.settings import TyperSettings
from wiederverwendbar.typer.sub import SubTyper


class Typer(_Typer):
    def __init__(self,
                 *,
                 title: Union[Default, str] = Default(),
                 description: Union[Default, str] = Default(),
                 version: Union[Default, str] = Default(),
                 terms_of_service: Union[None, Default, str] = Default(),
                 contact: Union[None, Default, dict[str, str]] = Default(),
                 license_info: Union[None, Default, dict[str, str]] = Default(),
                 info_enabled: Union[Default, bool] = Default(),
                 version_enabled: Union[Default, bool] = Default(),
                 name: Union[None, Default, str] = Default(),
                 help: Union[None, Default, str] = Default(),
                 settings: Optional[TyperSettings] = None,
                 branding_settings: Optional[BrandingSettings] = None,
                 console_settings: Optional[RichConsoleSettings] = None,
                 console: Optional[RichConsole] = None,
                 main_callback_parameters: Optional[list[inspect.Parameter]] = None,
                 **kwargs):

        # set default
        if settings is None:
            settings = TyperSettings()
        if branding_settings is None:
            branding_settings = BrandingSettings()
        if console_settings is None:
            console_settings = RichConsoleSettings()

        if type(title) is Default:
            title = settings.title
        if type(title) is Default:
            title = branding_settings.title
        if title is None:
            title = "Typer"

        if type(description) is Default:
            description = settings.description
        if type(description) is Default:
            description = branding_settings.description
        if type(description) is Default:
            description = ""

        if type(version) is Default:
            version = settings.version
        if type(version) is Default:
            version = branding_settings.version
        if type(version) is Default:
            version = Version("0.1.0")

        if type(terms_of_service) is Default:
            terms_of_service = settings.terms_of_service
        if type(terms_of_service) is Default:
            terms_of_service = branding_settings.terms_of_service
        if type(terms_of_service) is Default:
            terms_of_service = None

        if type(contact) is Default:
            contact = settings.contact
        if type(contact) is Default:
            if type(branding_settings.author) is str and type(branding_settings.author_email) is str:
                contact = {"name": branding_settings.author,
                           "email": branding_settings.author_email}
        if type(contact) is Default:
            contact = None

        if type(license_info) is Default:
            license_info = settings.license_info
        if type(license_info) is Default:
            if type(branding_settings.license) is str and type(branding_settings.license_url) is str:
                license_info = {"name": branding_settings.license,
                                "url": branding_settings.license_url}
        if type(license_info) is Default:
            license_info = None

        if type(info_enabled) is Default:
            info_enabled = settings.info_enabled
        if type(info_enabled) is Default:
            info_enabled = True

        if type(version_enabled) is Default:
            version_enabled = settings.version_enabled
        if type(version_enabled) is Default:
            version_enabled = True

        if type(name) is Default:
            name = settings.name
        if type(name) is Default:
            name = title

        if type(help) is Default:
            help = settings.help
        if type(help) is Default:
            help = description

        if console is None:
            console = RichConsole(settings=console_settings)

        if main_callback_parameters is None:
            main_callback_parameters = []

        super().__init__(name=name, help=help, **kwargs)

        # set attrs
        self.title = title
        self.description = description
        self.version = version
        self.terms_of_service = terms_of_service
        self.contact = contact
        self.license_info = license_info
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
        if self.contact is not None:
            if second_section != "":
                second_section += "\n"
            second_section += f"by {self.contact['name']}"
            if "email" in self.contact and self.contact["email"] != "":
                second_section += f" <{self.contact['email']}>"
        if second_section != "":
            second_section += "\n"
        second_section += f"Version: v{self.version}"
        if self.license_info is not None:
            second_section += f"\nLicense: {self.license_info['name']}"
            if "url" in self.license_info and self.license_info["url"] != "":
                second_section += f" -> {self.license_info['url']}"
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

    def add_typer(self, typer_instance: _Typer, **kwargs) -> None:
        super().add_typer(typer_instance, **kwargs)
        if isinstance(typer_instance, SubTyper):
            if typer_instance._parent is not None:
                if typer_instance._parent is not self:
                    raise ValueError("The SubTyper instance already has a parent assigned.")
            typer_instance._parent = self