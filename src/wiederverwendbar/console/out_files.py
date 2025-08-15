import sys
from enum import Enum
from typing import IO, Any, Union, Literal

OutFilesLiteral = Literal["stdout", "stderr"]


class OutFiles(str, Enum):
    """
    Output files
    """

    STDOUT = "stdout"
    STDERR = "stderr"

    def get_file(self) -> Union[IO[str], Any]:
        if self == OutFiles.STDOUT:
            return sys.stdout
        elif self == OutFiles.STDERR:
            return sys.stderr
        raise ValueError(f"Unknown outfile '{self}'.")
