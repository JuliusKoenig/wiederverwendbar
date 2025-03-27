import logging
import subprocess
import sys
from typing import Optional

from typing_extensions import Literal

logger = logging.getLogger(__name__)


def run_command(cmd: list[str],
                expected_exit_code: int = 0,
                encoding: Optional[str] = None,
                encoding_errors: Literal["strict", "ignore", "replace"] = "strict") -> tuple[bool, list[str], list[str]]:
    """
    Run a command and log its output.

    :param cmd: Command as list of strings
    :param expected_exit_code: Expected exit code of command
    :param encoding: Encoding of command output
    :param encoding_errors: Encoding error handling
    :return: True if command was successful, False otherwise
    """

    if encoding is None:
        if sys.platform == "win32":
            encoding = "cp437"
        else:
            encoding = "utf-8"

    cmd_str = " ".join(cmd)
    logger.debug(f"Run command: {cmd_str}")

    # run command
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # read output from pip command and log it
    stdout = []
    stderr = []
    with process.stdout and process.stderr:
        for line in iter(process.stdout.readline, b''):
            line_str = line.decode(encoding=encoding, errors=encoding_errors).strip()
            logger.debug("stdout: " + line_str)
            stdout.append(line_str)

        for line in iter(process.stderr.readline, b''):
            line_str = line.decode(encoding=encoding, errors=encoding_errors).strip()
            logger.debug("stderr: " + line_str)
            stderr.append(line_str)

    exit_code = process.wait()

    # check exit status
    if exit_code != expected_exit_code:
        logger.error(f"Command '{cmd_str}' has exit status '{exit_code}' but expected exit status is '{expected_exit_code}'.")
        return False, stdout, stderr

    return True, stdout, stderr
