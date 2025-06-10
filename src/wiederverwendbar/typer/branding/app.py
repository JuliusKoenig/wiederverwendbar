import inspect
from typing import Optional, Annotated

from typer import Option, Exit
from art import text2art

from wiederverwendbar.rich import RichConsole
from wiederverwendbar.typer.app import Typer
from wiederverwendbar.typer.branding.settings import TyperBrandingSettings


class TyperBranding(Typer):
    def __init__(self,
                 *,
                 name: Optional[str] = None,
                 help: Optional[str] = None,
                 title: Optional[str] = None,
                 description: Optional[str] = None,
                 version: Optional[str] = None,
                 author: Optional[str] = None,
                 author_email: Optional[str] = None,
                 license: Optional[str] = None,
                 license_url: Optional[str] = None,
                 terms_of_service: Optional[str] = None,
                 info_enabled: Optional[bool] = None,
                 version_enabled: Optional[bool] = None,
                 settings: Optional[TyperBrandingSettings] = None,
                 console: Optional[RichConsole] = None,
                 main_callback_parameters: Optional[list[inspect.Parameter]] = None,
                 **kwargs):

        # set default
        if settings is None:
            settings = TyperBrandingSettings()
        if title is None:
            title = settings.branding_title
        if description is None:
            description = settings.branding_description
        if version is None:
            version = settings.branding_version
        if author is None:
            author = settings.branding_author
        if author_email is None:
            author_email = settings.branding_author_email
        if license is None:
            license = settings.branding_license
        if license_url is None:
            license_url = settings.branding_license_url
        if terms_of_service is None:
            terms_of_service = settings.branding_terms_of_service
        if info_enabled is None:
            info_enabled = settings.cli_info_enabled
        if version_enabled is None:
            version_enabled = settings.cli_version_enabled
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

        card_body = [text2art(title),
                     f"{description}\n"
                     f"by {author} ({author_email})\n"
                     f"Version: v{version}\n"
                     f"License: {license} - {license_url}\n"
                     f"Terms of Service: {terms_of_service}"]

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
