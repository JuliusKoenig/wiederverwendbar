import logging
import subprocess

logger = logging.getLogger(__name__)


def run_command(cmd: list[str], expected_exit_code=0) -> tuple[bool, list[str], list[str]]:
    """
    Run a command and log its output.

    :param cmd: Command as list of strings
    :param expected_exit_code: Expected exit code of command
    :return: True if command was successful, False otherwise
    """

    cmd_str = " ".join(cmd)
    logger.debug(f"Run command: {cmd_str}")

    # run command
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # read output from pip command and log it
    stdout = []
    stderr = []
    with process.stdout and process.stderr:
        for line in iter(process.stdout.readline, b''):
            line_str = line.decode("cp437").strip()
            logger.debug("stdout: " + line_str)
            stdout.append(line_str)

        for line in iter(process.stderr.readline, b''):
            line_str = line.decode("cp437").strip()
            logger.debug("stderr: " + line_str)
            stderr.append(line_str)

    exit_code = process.wait()

    # check exit status
    if exit_code != expected_exit_code:
        logger.error(f"Command '{cmd_str}' has exit status '{exit_code}' but expected exit status is '{expected_exit_code}'.")
        return False, stdout, stderr

    return True, stdout, stderr
