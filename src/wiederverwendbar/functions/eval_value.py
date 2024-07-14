import logging
import os
from pathlib import Path
from typing import Any, Union, Optional

logger = logging.getLogger(__name__)


def eval_value(what: str,
               value: Union[str, Path, list[str]],
               index_marker: Optional[list[str]] = None,
               use_environ: bool = True,
               **_local_vars) -> Union[str, Path, list[Union[str, Path]]]:
    """
    Evaluate value with variables.

    :param what: Message to log
    :param value: Value to evaluate
    :param index_marker: Index marker
    :param use_environ: Use environment variables
    :param _local_vars: Variables to use
    :return: Evaluated value
    """

    # if index_marker is None, take default value
    if index_marker is None:
        index_marker = ["{{", "}}"]

    # check if len of index_marker is 2
    if len(index_marker) != 2:
        logger.error("Index marker must have a length of 2.")
        raise RuntimeError("Index marker must have a length of 2.")

    logger.debug(f"Evaluate {what}")

    def update_local_vars(_key: str, _value: Any) -> None:
        if _key in _local_vars:
            logger.error(f"Variable '{_key}' is reserved and cannot be used.")
            raise RuntimeError(f"Variable '{_key}' is reserved and cannot be used.")
        _local_vars[_key] = _value

    # add env to local_vars
    if use_environ:
        update_local_vars("env", dict(os.environ))

    as_list = True
    if not isinstance(value, list):
        value = [value]
        as_list = False

    def _format(_value: str) -> str:
        if type(_value) is not str:
            _value = str(_value)
        locals().update(_local_vars)
        if index_marker[0] in _value and index_marker[1] in _value:
            _start_index = _value.find(index_marker[0])
            _end_index = _value.find(index_marker[1])
            _expression = str(_value[_start_index + len(index_marker[0]):_end_index])
            _expression_value = eval(_expression)
            _expression_value_str = str(_expression_value)
            _solved_value = _value[:_start_index] + _expression_value_str + _value[_end_index + len(index_marker[1]):]
            return _format(_solved_value)
        else:
            return _value

    evaluated_values = []
    for v in value:
        try:
            if isinstance(v, Path):
                evaluated_v_path = Path()
                for part in v.parts:
                    evaluated_v = _format(part)
                    evaluated_v_path = evaluated_v_path / evaluated_v
                evaluated_v = evaluated_v_path
            else:
                evaluated_v = _format(v)
            evaluated_values.append(evaluated_v)
        except Exception as e:
            logger.error(f"Could not evaluate {what} '{v}'. -> {e}")
            raise RuntimeError(f"Could not evaluate {what} '{v}'. -> {e}")

    if len(evaluated_values) == 0:
        logger.error(f"Could not evaluate {what}. -> Empty list")
        raise RuntimeError(f"Could not evaluate {what}. -> Empty list")

    if not as_list:
        evaluated_values = evaluated_values[0]

    logger.debug(f"Evaluated {what} is: '{evaluated_values}'")

    return evaluated_values
