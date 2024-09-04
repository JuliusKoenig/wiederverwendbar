import logging
import os
from collections.abc import Iterator
from enum import Enum
from pathlib import Path
from typing import Optional, Union

import requests

from wiederverwendbar.functions.check_hash_file import SUPPORTED_HASH_TYPES, check_hash_file

logger = logging.getLogger(__name__)


class DownloadFileState(Enum):
    START = 0
    DOWNLOAD = 1
    CHECK_HASH = 2
    END = 3


def download_file(download_url: str,
                  local_file: Union[None, str, Path] = None,
                  hash_value: Optional[str] = None,
                  hash_type: Optional[SUPPORTED_HASH_TYPES] = None,
                  method: Optional[str] = None,
                  overwrite: Optional[bool] = None,
                  chunk_size: Optional[int] = None,
                  yield_percent: Optional[bool] = None) -> Iterator[Union[DownloadFileState, int]]:
    """
    Download single file with requests module.

    :param download_url: for example https://www.example.com/test.bin
    :param local_file: file on disk (default: basename of download_url)
    :param hash_value: hash value for file
    :param hash_type: hash type for file
    :param method: GET or POST (default: GET)
    :param overwrite: overwrite local file (default: False)
    :param chunk_size: download chunk size (default: 1024)
    :param yield_percent: yield percent instead of bytes (default: True)
    :return: generator
    """

    logger.debug(f"Download file: {download_url}")

    # set default values
    if method is None:
        method = "GET"
    if overwrite is None:
        overwrite = False
    if chunk_size is None:
        chunk_size = 1024
    if yield_percent is None:
        yield_percent = True

    # parse download_url
    if local_file is None:
        local_file = os.path.basename(requests.utils.urlparse(download_url).path)
    if local_file == "":
        raise ValueError("Can't parse download_url")
    local_file = Path(local_file)

    # check if file exists
    if local_file.exists():
        if not overwrite:
            raise FileExistsError("File exists")
        logger.debug(f"Overwrite file: {local_file}")
        local_file.unlink()

    # yield start value
    logger.debug(f"Start download: {download_url} -> {local_file}")
    yield DownloadFileState.START

    response = requests.request(method=method, url=download_url, stream=True)
    total = int(response.headers.get("content-length", 0))
    bytes_downloaded = 0
    percent_downloaded = 0

    # yield start and end value
    yield 0
    if yield_percent:
        yield 100
    else:
        yield total

    # yield download value
    logger.debug(f"Download file: {download_url} -> {local_file}")
    yield DownloadFileState.DOWNLOAD

    # download file
    with open(local_file, "wb") as f:
        for data in response.iter_content(chunk_size=chunk_size):
            f.write(data)
            bytes_downloaded += len(data)
            if total > 0:
                if yield_percent:
                    percent = round(bytes_downloaded / total * 100)
                    if percent != percent_downloaded:
                        percent_downloaded = percent
                        yield percent_downloaded
                else:
                    yield bytes_downloaded

    if hash_value is not None:
        # yield check hash value
        logger.debug(f"Check hash: {download_url} -> {local_file}")
        yield DownloadFileState.CHECK_HASH

        # check hash value
        if not check_hash_file(local_file, hash_value, hash_type):
            raise ValueError("Hash value not correct")

    # yield end value
    logger.debug(f"End download: {download_url} -> {local_file}")
    yield DownloadFileState.END


def simple_download_file(download_url: str,
                         local_file: Union[None, str, Path] = None,
                         hash_value: Optional[str] = None,
                         hash_type: Optional[SUPPORTED_HASH_TYPES] = None,
                         method: Optional[str] = None,
                         overwrite: Optional[bool] = None,
                         chunk_size: Optional[int] = None,
                         raise_exception: Optional[bool] = None) -> bool:
    """
    Download single file with requests module.

    :param download_url: for example https://www.example.com/test.bin
    :param local_file: file on disk (default: basename of download_url)
    :param hash_value: hash value for file
    :param hash_type: hash type for file
    :param method: GET or POST (default: GET)
    :param overwrite: overwrite local file (default: False)
    :param chunk_size: download chunk size (default: 1024)
    :param raise_exception: raise exception on error (default: True)
    :return: True if download was successful, False otherwise
    """

    # set default values
    if raise_exception is None:
        raise_exception = True

    try:
        for state in download_file(download_url=download_url,
                                   hash_value=hash_value,
                                   hash_type=hash_type,
                                   method=method,
                                   local_file=local_file,
                                   overwrite=overwrite,
                                   chunk_size=chunk_size):
            if state == DownloadFileState.END:
                return True
    except Exception as e:
        if raise_exception:
            raise e
        logger.exception(e)

    return False
