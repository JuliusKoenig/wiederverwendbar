import json
from typing import Any, Callable

from wiederverwendbar.pydantic.file.base import BaseFile


class JsonFile(BaseFile):
    class Config:
        file_suffix = ".json"
        file_json_decoder_cls = None
        file_json_decode_object_hook = None
        file_json_decode_parse_float = None
        file_json_decode_parse_int = None
        file_json_decode_parse_constant = None
        file_json_decode_object_pairs_hook = None
        file_json_encode_skip_keys = False
        file_json_encode_ensure_ascii = True
        file_json_encode_check_circular = True
        file_json_encode_allow_nan = True
        file_json_encoder_cls = None
        file_json_encode_indent = None
        file_json_encode_separators = None
        file_json_encode_default = None
        file_json_encode_sort_keys = False

    class _InstanceConfig(BaseFile._InstanceConfig):
        """
        Instance configuration for json file handling.

        Attributes:
            file_json_decoder_cls (type[json.JSONDecoder] | None): Custom JSONDecoder class to use for decoding JSON content.
            file_json_decode_object_hook (Callable[[dict[Any, Any]], Any | None] | None): Function to transform decoded JSON objects (dictionaries).
            file_json_decode_parse_float (Callable[[str], Any | None] | None): Function to parse JSON float values.
            file_json_decode_parse_int (Callable[[str], Any | None] | None): Function to parse JSON integer values.
            file_json_decode_parse_constant (Callable[[str], Any | None] | None): Function to handle special JSON constants like NaN and Infinity.
            file_json_decode_object_pairs_hook (Callable[[list[tuple[Any, Any]]], Any | None] | None): Function to transform decoded JSON object pairs (list of tuples).
            file_json_encode_skip_keys (bool): Whether to skip keys that are not basic types (str, int, float, bool, None) during encoding.
            file_json_encode_ensure_ascii (bool): Whether to escape non-ASCII characters in the output JSON string.
            file_json_encode_check_circular (bool): Whether to check for circular references during encoding.
            file_json_encode_allow_nan (bool): Whether to allow NaN and Infinity values in the output JSON string.
            file_json_encoder_cls (type[json.JSONEncoder] | None): Custom JSONEncoder class to use for encoding Python objects to JSON.
            file_json_encode_indent (None | int | str): Indentation level for pretty-printing the output JSON string. If None, the most compact representation is used.
            file_json_encode_separators (tuple[str, str] | None): Tuple specifying how to separate items and key-value pairs in the output JSON string. If None, defaults to (', ', ': ').
            file_json_encode_default (Callable[[...], Any | None] | None): Function to handle objects that are not serializable by default.
            file_json_encode_sort_keys (bool): Whether to sort the keys in the output JSON string.
        """

        file_json_decoder_cls: type[json.JSONDecoder] | None
        file_json_decode_object_hook: Callable[[dict[Any, Any]], Any | None] | None
        file_json_decode_parse_float: Callable[[str], Any | None] | None
        file_json_decode_parse_int: Callable[[str], Any | None] | None
        file_json_decode_parse_constant: Callable[[str], Any | None] | None
        file_json_decode_object_pairs_hook: Callable[[list[tuple[Any, Any]]], Any | None] | None
        file_json_encode_skip_keys: bool
        file_json_encode_ensure_ascii: bool
        file_json_encode_check_circular: bool
        file_json_encode_allow_nan: bool
        file_json_encoder_cls: type[json.JSONEncoder] | None
        file_json_encode_indent: None | int | str
        file_json_encode_separators: tuple[str, str] | None
        file_json_encode_default: Callable[[...], Any | None] | None
        file_json_encode_sort_keys: bool

    @property
    def config(self) -> _InstanceConfig:
        return super().config

    @classmethod
    def _to_dict(cls, content: str, config: _InstanceConfig) -> dict:
        data = json.loads(content,
                          cls=config.file_json_decoder_cls,
                          object_hook=config.file_json_decode_object_hook,
                          parse_float=config.file_json_decode_parse_float,
                          parse_int=config.file_json_decode_parse_int,
                          parse_constant=config.file_json_decode_parse_constant,
                          object_pairs_hook=config.file_json_decode_object_pairs_hook)
        return data

    def _from_dict(self, data: dict[str, Any], config: _InstanceConfig) -> str:
        content = json.dumps(data,
                             skipkeys=config.file_json_encode_skip_keys,
                             ensure_ascii=config.file_json_encode_ensure_ascii,
                             check_circular=config.file_json_encode_check_circular,
                             allow_nan=config.file_json_encode_allow_nan,
                             cls=config.file_json_encoder_cls,
                             indent=config.file_json_encode_indent,
                             separators=config.file_json_encode_separators,
                             default=config.file_json_encode_default,
                             sort_keys=config.file_json_encode_sort_keys)
        return content
