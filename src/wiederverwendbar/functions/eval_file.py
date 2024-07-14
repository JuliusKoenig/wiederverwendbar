import logging
from pathlib import Path
from typing import Optional

from wiederverwendbar.functions.eval_value import eval_value

logger = logging.getLogger(__name__)


def eval_file(src_file_path: Path, **locals_vars) -> Optional[str]:
    """
    Evaluate file with variables.

    :param src_file_path Source file path
    :param locals_vars: Variables to use
    :return: Evaluated file
    """

    logger.debug(f"Evaluate file '{src_file_path}'")

    # check if file exists
    if not src_file_path.is_file():
        logger.error(f"File '{src_file_path}' does not exist.")
        return None

    # read file
    with open(src_file_path, 'r') as f:
        src_file_raw = f.read()
        # split lines
        src_file_lines = src_file_raw.splitlines()

    # eval line by line
    evaluated_lines = []
    current_line = 1
    for line in src_file_lines:
        try:
            evaluated_line = eval_value(what=f"line '{current_line}' in file '{src_file_path}'",
                                        value=line,
                                        **locals_vars)
            evaluated_lines.append(evaluated_line)
        except Exception as e:
            logger.debug(f"Could not evaluate line {current_line} '{line}'. -> {e}")
            raise RuntimeError(f"Could not evaluate line {current_line} '{line}'. -> {e}")
        current_line += 1

    # join lines
    evaluated = "\n".join(evaluated_lines)

    logger.debug(f"Evaluated file '{src_file_path}':\n{evaluated}")

    return evaluated
