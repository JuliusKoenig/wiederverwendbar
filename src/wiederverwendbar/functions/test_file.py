import tempfile
from pathlib import Path
from typing import Literal

AVAILABLE_UNITS = Literal['B', 'KB', 'MB', 'GB']


def test_file(size: int = 1, unit: AVAILABLE_UNITS = 'MB') -> Path:
    """
    Generate a test file with the given size and unit.

    :param size: Size of the file
    :param unit: Unit of the size
    :return: Path to the generated file
    """

    if unit == 'B':
        file_size_in_bytes = size
    elif unit == 'KB':
        file_size_in_bytes = size * 1024
    elif unit == 'MB':
        file_size_in_bytes = size * 1024 * 1024
    elif unit == 'GB':
        file_size_in_bytes = size * 1024 * 1024 * 1024
    else:
        raise ValueError('Invalid unit')

    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf.seek(file_size_in_bytes - 1)
        tf.write(b'0')

        return Path(tf.name)
