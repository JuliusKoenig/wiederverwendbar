from enum import Enum


class TerminalOutFiles(str, Enum):
    """
    Terminal output files
    """

    STDOUT = "stdout"
    STDERR = "stderr"
