import inspect
from typing import Optional

import typer

from wiederverwendbar.rich.console import RichConsole
from wiederverwendbar.typer.settings import TyperSettings


class TyperApp(typer.Typer):
    def __init__(self,
                 *,
                 name: Optional[str] = None,
                 help: Optional[str] = None,
                 settings: Optional[TyperSettings] = None,
                 console: Optional[RichConsole] = None,
                 main_callback_parameters: Optional[list[inspect.Parameter]] = None,
                 **kwargs):

        # set default
        if settings is None:
            settings = TyperSettings()
        if name is None:
            name = settings.cli_name
        if help is None:
            help = settings.cli_help
        if console is None:
            console = RichConsole(settings=settings)
        if main_callback_parameters is None:
            main_callback_parameters = []

        super().__init__(name=name, help=help, **kwargs)

        # set console
        self.console = console

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

    def main_callback(self, *args, **kwargs):
        ...
