from wiederverwendbar.console.out_files import OutFiles
from wiederverwendbar.printable_settings import PrintableSettings, Field


class ConsoleSettings(PrintableSettings):
    file: OutFiles = Field(default=OutFiles.STDOUT,
                           title="Console File",
                           description="The file to write the console output to.")
    seperator: str = Field(default=" ",
                           title="Console Separator",
                           description="The separator to be used between values.")
    end: str = Field(default="\n",
                     title="Console End",
                     description="The end to be used after the last value.")
    exclamation_prefix_brackets_style: str = Field(default="square",
                                                   title="Console Exclamation Bracket Style",
                                                   description="The style to be used for the exclamation brackets.")
