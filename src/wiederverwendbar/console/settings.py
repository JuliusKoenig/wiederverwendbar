from pydantic import BaseModel, Field

from wiederverwendbar.console.out_files import OutFiles


class ConsoleSettings(BaseModel):
    console_file: OutFiles = Field(default=OutFiles.STDOUT, title="Console File", description="The file to write the console output to.")
    console_seperator: str = Field(default=" ", title="Console Separator", description="The separator to be used between values.")
    console_end: str = Field(default="\n", title="Console End", description="The end to be used after the last value.")
