from rich.console import Console

from wiederverwendbar.rich.settings import RichConsoleSettings


class RichConsole(Console):
    def __init__(self, *, settings: RichConsoleSettings, **kwargs):
        settings_dict = {}
        for key, value in settings.model_dump().items():
            if key.startswith("console_"):
                key = key[len("console_"):]
            settings_dict[key] = value
        settings_dict.update(kwargs)
        super().__init__(**settings_dict)
