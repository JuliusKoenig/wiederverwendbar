import typing
import warnings
import logging
from pathlib import Path
from typing import Optional, Union, Literal

logger = logging.getLogger(__name__)


# define warning ...
class HashTypeIsNoneWarning(Warning):
    pass


SUPPORTED_HASH_TYPES = Literal["md5", "sha1", "sha256", "sha512"]
SUPPORTED_HASH_TYPES_TUPLE: tuple[SUPPORTED_HASH_TYPES, ...] = typing.get_args(SUPPORTED_HASH_TYPES)


def check_hash_file(check_file: Union[str, Path],
                    hash_value: str,
                    hash_type: Optional[SUPPORTED_HASH_TYPES] = None) -> bool:
    """
    Check single file with hash value.

    :param check_file: file on disk
    :param hash_value: hash value for file
    :param hash_type: hash type for file, if None all hash types are checked(slows down the check)
    :return: True on success, False on fail
    """

    if hash_type is None:
        warnings.warn("No hash type specified, all hash types are checked. Define hash_type for better performance or suppress this warning.", HashTypeIsNoneWarning)

    if type(check_file) == str:
        check_file = Path(check_file)

    logger.debug(f"Check file: {check_file}")

    # check if file exists
    if not check_file.is_file():
        raise FileNotFoundError("File not found")

    def check_hash(ht: SUPPORTED_HASH_TYPES) -> bool:
        if ht == "md5":
            import hashlib
            h = hashlib.md5()
        elif ht == "sha1":
            import hashlib
            h = hashlib.sha1()
        elif ht == "sha256":
            import hashlib
            h = hashlib.sha256()
        elif ht == "sha512":
            import hashlib
            h = hashlib.sha512()
        else:
            raise ValueError("Unknown hash type")
        with open(check_file, "rb") as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                h.update(data)
        result = h.hexdigest() == hash_value
        logger.debug(f"Check hash: {ht} -> {result}")
        return result

    # check if hash_type is None
    if hash_type is None:
        for ht in SUPPORTED_HASH_TYPES_TUPLE:
            if check_hash(ht):
                return True
    else:
        if check_hash(hash_type):
            return True
    return False
