import inspect
from typing import Optional, Annotated, Union

from typer import Option, Exit
from art import text2art

from wiederverwendbar.default import Default
from wiederverwendbar.rich import RichConsole
from wiederverwendbar.typer.app import Typer
from wiederverwendbar.typer.branding.settings import TyperBrandingSettings


class TyperBranding(Typer):
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
                 settings: Optional[TyperBrandingSettings] = None,
                 console: Optional[RichConsole] = None,
                 main_callback_parameters: Optional[list[inspect.Parameter]] = None,
                 **kwargs):

        # set default
        if settings is None:
            settings = TyperBrandingSettings()
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
        if main_callback_parameters is None:
            main_callback_parameters = []

        # add info command parameter to main_callback_parameters
        if info_enabled:
            def info_callback(value: bool) -> None:
                if not value:
                    return
                code = self.info_command(title=title,
                                         description=description,
                                         version=version,
                                         author=author,
                                         author_email=author_email,
                                         license=license,
                                         license_url=license_url,
                                         terms_of_service=terms_of_service)
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
                code = self.version_command(title=title,
                                            version=version)
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

        super().__init__(name=name,
                         help=help,
                         settings=settings,
                         console=console,
                         main_callback_parameters=main_callback_parameters,
                         **kwargs)

    def info_command(self,
                     title: str,
                     description: Optional[str],
                     version: str,
                     author: Optional[str],
                     author_email: Optional[str],
                     license: Optional[str],
                     license_url: Optional[str],
                     terms_of_service: Optional[str]) -> Optional[int]:
        card_body = [text2art(title)]
        second_section = ""
        if description is not None:
            second_section += f"{description}"
        if author is not None:
            if second_section != "":
                second_section += "\n"
            second_section += f"by {author}"
            if author_email is not None:
                second_section += f" ({author_email})"
        if second_section != "":
            second_section += "\n"
        second_section += f"Version: v{version}"
        if license is not None:
            second_section += f"\nLicense: {license}"
            if license_url is not None:
                second_section += f" - {license_url}"
        if terms_of_service is not None:
            second_section += f"\nTerms of Service: {terms_of_service}"
        card_body.append(second_section)

        self.console.card(*card_body,
                          padding_left=1,
                          padding_right=1,
                          border_style="double_line",
                          color="white",
                          border_color="blue")

    def version_command(self,
                        title: str,
                        version: Optional[str]) -> Optional[int]:
        self.console.print(f"{title} v[cyan]{version}[/cyan]")
