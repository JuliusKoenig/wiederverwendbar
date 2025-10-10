from typing import Any, Callable

try:
    from tomllib import loads, dumps
except ImportError:
    # ToDo: Remove when dropping support for Python < 3.11
    from pip._vendor.tomli import loads
    from pip._vendor.tomli_w import dumps

from wiederverwendbar.pydantic.file.base import BaseFile


class TomlFile(BaseFile):
    class Config:
        file_suffix = ".toml"
        file_toml_decode_parse_float = float
        file_toml_encode_multiline_strings = False
        file_toml_encode_indent = 4

    class _InstanceConfig(BaseFile._InstanceConfig):
        """
        Instance configuration for json file handling.

        Attributes:
            file_toml_decode_parse_float (Callable[[str], Any]): Function to parse float values during decoding. Default is the built-in float function.
            file_toml_encode_multiline_strings (bool): Whether to encode strings as multiline strings when possible. Default is False.
            file_toml_encode_indent (int | None): Indentation level for pretty-printing the TOML output. If None, no pretty-printing is applied. Default is 4.
        """

        file_toml_decode_parse_float: Callable[[str], Any]
        file_toml_encode_multiline_strings: bool
        file_toml_encode_indent: int | None

    @property
    def config(self) -> _InstanceConfig:
        return super().config

    @classmethod
    def _to_dict(cls, content: str, config: _InstanceConfig) -> dict:
        data = loads(content,
                     parse_float=config.file_toml_decode_parse_float)
        return data

    def _from_dict(self, data: dict[str, Any], config: _InstanceConfig) -> str:
        content = dumps(data,
                        multiline_strings=config.file_toml_encode_multiline_strings,
                        indent=0 if config.file_toml_encode_indent is None else config.file_toml_encode_indent)
        return content
